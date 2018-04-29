# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from openerp import models, fields, api, _
from openerp import workflow
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.addons.hotel import date_utils
import pytz
import time
import logging
_logger = logging.getLogger(__name__)


class FolioWizard(models.TransientModel):
    _name = 'hotel.folio.wizard'

    @api.multi
    def _get_default_checkin(self):
        folio = False
        default_arrival_hour = self.env['ir.values'].get_default(
                'hotel.config.settings', 'default_arrival_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        else:
            tz_hotel = self.env['ir.values'].get_default(
                'hotel.config.settings', 'tz_hotel')
            now_utc_dt = date_utils.now()
            ndate = "%s %s:00" % \
                (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 default_arrival_hour)
            ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_default_checkout(self):
        folio = False
        default_departure_hour = self.env['ir.values'].get_default(
            'hotel.config.settings', 'default_departure_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([
                ('id', '=', self._context['folio_id'])
            ])
        if folio and folio.room_lines:
                        return folio.room_lines[0].checkout
        else:
            tz_hotel = self.env['ir.values'].get_default(
                'hotel.config.settings', 'tz_hotel')
            now_utc_dt = date_utils.now() + timedelta(days=1)
            ndate = "%s %s:00" % \
                (now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 default_departure_hour)
            ndate_dt = date_utils.get_datetime(ndate, stz=tz_hotel)
            ndate_dt = date_utils.dt_as_timezone(ndate_dt, 'UTC')
            return ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    partner_id = fields.Many2one('res.partner',string="Customer")
    checkin = fields.Datetime('Check In', required=True,
                              default=_get_default_checkin)
    checkout = fields.Datetime('Check Out', required=True,
                               default=_get_default_checkout)
    rooms_num = fields.Integer('Number of Rooms')
    max_rooms = fields.Integer('Max', readonly=True)
    virtual_room_id = fields.Many2one('hotel.virtual.room',
                                      string="Virtual Rooms")
    reservation_wizard_ids = fields.One2many('hotel.reservation.wizard',
                                             'folio_wizard_id',
                                             string="Resevations")
    total = fields.Float('Total', compute='_computed_total')
    confirm = fields.Boolean('Confirm Reservations', default="1")
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('web', 'Web'),
    ], 'Sales Channel')

    @api.multi
    @api.onchange('checkin', 'checkout')
    def onchange_checks(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        self.ensure_one()
        now_utc_dt = date_utils.now()
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # UTC -> Hotel tz
        tz = self.env['ir.values'].get_default('hotel.config.settings',
                                               'tz_hotel')
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)

        if chkin_utc_dt >= chkout_utc_dt:
            dpt_hour = self.env['ir.values'].get_default(
                'hotel.config.settings', 'default_departure_hour')
            checkout_str = (chkin_utc_dt + timedelta(days=1)).strftime(
                                                    DEFAULT_SERVER_DATE_FORMAT)
            checkout_str = "%s %s:00" % (checkout_str, dpt_hour)
            checkout_dt = date_utils.get_datetime(checkout_str, stz=tz)
            checkout_utc_dt = date_utils.dt_as_timezone(checkout_dt, 'UTC')
            self.checkout = checkout_utc_dt.strftime(
                                                DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_dt = date_utils.get_datetime(self.checkout, stz=tz)
        # Reservation end day count as free day. Not check it
        checkout_dt -= timedelta(days=1)
        occupied = self.env['hotel.reservation'].occupied(
            self.checkin,
            checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
        rooms_occupied = occupied.mapped('product_id.id')
        free_rooms = self.env['hotel.room'].search([
            ('product_id.id', 'not in', rooms_occupied)
        ])
        free_virtual_ids = free_rooms.mapped('price_virtual_room.id')
        domain_rooms = [('id', 'in', free_virtual_ids)]
        return {'domain': {'virtual_room_id': domain_rooms}}

    @api.onchange('virtual_room_id')
    def onchange_virtual_room_id(self):
        self.ensure_one()
        if self.virtual_room_id and self.checkin and self.checkout:
            checkout_dt = date_utils.get_datetime(self.checkout)
            # Reservation end day count as free day. Not check it
            checkout_dt -= timedelta(days=1)
            self.max_rooms = len(
                self.virtual_room_id.check_availability_virtual_room(
                        self.checkin,
                        checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        self.virtual_room_id.id)
                        )

    @api.onchange('rooms_num')
    def onchange_rooms_num(self):
        self.ensure_one()
        if self.rooms_num > self.max_rooms:
            raise ValidationError(_("Too many rooms!"))
        elif self.virtual_room_id:
            cmds = []
            total = 0
            checkout_dt = date_utils.get_datetime(self.checkout)
            checkout_dt -= timedelta(days=1)
            occupied = self.env['hotel.reservation'].occupied(
                self.checkin,
                checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            rooms_occupied = occupied.mapped('product_id.id')
            free_rooms = self.env['hotel.room'].search([
                ('product_id.id', 'not in', rooms_occupied),
                ('price_virtual_room.id', '=', self.virtual_room_id.id)],
                order='sequence', limit=self.rooms_num)
            room_ids = free_rooms.mapped('product_id.id')
            product_list = self.env['product.product'].search([
                ('id', 'in', room_ids)
            ])
            nights = days_diff = date_utils.date_diff(self.checkin,
                                                      self.checkout,
                                                      hours=False)
            hotel_tz = self.env['ir.values'].sudo().get_default(
                'hotel.config.settings',
                'hotel_tz')
            start_date_utc_dt = date_utils.get_datetime(self.checkin)
            start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt,
                                                      hotel_tz)
            for line in self.reservation_wizard_ids:
                line.amount_reservation = line.price
                cmds.append((4, line.id))
                total += line.price
            for room in product_list:
                pricelist_id = self.env['ir.values'].sudo().get_default(
                    'hotel.config.settings', 'parity_pricelist_id')
                if pricelist_id:
                    pricelist_id = int(pricelist_id)
                res_price = 0
                res_partner = self.partner_id or self.env['res.partner'].browse('1')
                for i in range(0, nights):
                    ndate = start_date_dt + timedelta(days=i)
                    ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    prod = self.virtual_room_id.product_id.with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id.id,
                        quantity=1,
                        date=ndate_str,
                        pricelist=pricelist_id,
                        uom=room.uom_id.id)
                    res_price += prod.price
                adults = self.env['hotel.room'].search([
                    ('product_id.id', '=', room.id)
                ]).capacity
                total += res_price
                cmds.append((0, False, {
                            'checkin': self.checkin,
                            'checkout': self.checkout,
                            'product_id': room.id,
                            'nights': nights,
                            'adults': adults,
                            'children': 0,
                            'virtual_room_id': self.virtual_room_id,
                            'price': res_price,
                            'amount_reservation': res_price
                        }))
            self.reservation_wizard_ids = cmds
            self.virtual_room_id = ''
            self.rooms_num = 0
            self.total = total

    @api.depends('reservation_wizard_ids')
    def _computed_total(self):
        total = 0
        for line in self.reservation_wizard_ids:
            total += line.price
        self.total = total

    @api.multi
    def create_folio(self):
        self.ensure_one()
        if not self.partner_id:
               raise ValidationError(_("We need know the customer!"))
        reservations = [(5, False, False)]
        for line in self.reservation_wizard_ids:
            reservations.append((0, False, {
                        'product_id': line.product_id.id,
                        'adults': line.adults,
                        'children': line.children,
                        'checkin': line.checkin,
                        'checkout': line.checkout,
                        'virtual_room_id': line.virtual_room_id.id,
                    }))
        vals = {
                'partner_id': self.partner_id.id,
                'channel_type': self.channel_type,
                'room_lines': reservations,
            }
        newfol = self.env['hotel.folio'].create(vals)
        for room in newfol.room_lines:
            room.on_change_checkin_checkout_product_id()
        newfol.compute_invoices_amount()
        if self.confirm:
            newfol.action_confirm()


class ReservationWizard(models.TransientModel):
    _name = 'hotel.reservation.wizard'

    product_id = fields.Many2one('product.product',
                                string="Virtual Rooms")

    folio_wizard_id = fields.Many2one('hotel.folio.wizard')

    adults = fields.Integer('Adults',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children',
                              help='Number of children there in guest list.')
    checkin = fields.Datetime('Check In', required=True)
    checkout = fields.Datetime('Check Out', required=True)
    virtual_room_id = fields.Many2one('hotel.virtual.room',
                                      string='Virtual Room Type',
                                      required=True)
    nights = fields.Integer('Nights', readonly=True)
    price = fields.Float(string='Total')
    amount_reservation = fields.Float(string='Total', readonly=True)
    partner_id = fields.Many2one(related='folio_wizard_id.partner_id')

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if line.checkin and line.checkout:
                room = self.env['hotel.room'].search([
                    ('product_id.id','=',line.product_id.id)
                ])
                if line.adults == 0:
                    line.adults = room.capacity
                line.virtual_room_id = room.price_virtual_room.id
                checkout_dt = date_utils.get_datetime(line.checkout)
                checkout_dt -= timedelta(days=1)
                occupied = self.env['hotel.reservation'].occupied(
                    line.checkin,
                    checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                rooms_occupied = occupied.mapped('product_id.id')
                if line.product_id.id in rooms_occupied:
                    raise ValidationError(_("This room is occupied!, please, choice other room or change the reservation date"))

    @api.multi
    @api.onchange('checkin', 'checkout', 'virtual_room_id')
    def onchange_dates(self):
        for line in self:
            if not self.checkin:
                self.checkin = self.folio_wizard_id.checkin
            if not self.checkout:
                self.checkout = self.folio_wizard_id.checkout

            hotel_tz = self.env['ir.values'].sudo().get_default(
                'hotel.config.settings', 'hotel_tz')
            start_date_utc_dt = date_utils.get_datetime(line.checkin)
            start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt,
                                                      hotel_tz)

            if line.virtual_room_id:
                pricelist_id = self.env['ir.values'].sudo().get_default(
                    'hotel.config.settings', 'parity_pricelist_id')
                if pricelist_id:
                    pricelist_id = int(pricelist_id)
                nights = days_diff = date_utils.date_diff(line.checkin,
                                                          line.checkout,
                                                          hours=False)
                res_price = 0
                res_partner = self.partner_id or self.env['res.partner'].browse('1')
                for i in range(0, nights):
                    ndate = start_date_dt + timedelta(days=i)
                    ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    prod = line.virtual_room_id.product_id.with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id.id,
                        quantity=1,
                        date=ndate_str,
                        pricelist=pricelist_id,
                        uom=line.product_id.uom_id.id)
                    res_price += prod.price
                adults = self.env['hotel.room'].search([
                    ('product_id.id', '=', line.product_id.id)
                ]).capacity
                line.amount_reservation = res_price
                line.price = res_price
            checkout_dt = date_utils.get_datetime(self.checkout)
            checkout_dt -= timedelta(days=1)
            occupied = self.env['hotel.reservation'].occupied(
                self.checkin,
                checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            rooms_occupied = occupied.mapped('product_id.id')
            domain_rooms = [
                ('isroom', '=', True),
                ('id', 'not in', rooms_occupied)
            ]
            return {'domain': {'product_id': domain_rooms}}

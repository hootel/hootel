# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Dario Lodeiros <>
#                       Alexandre Díaz <dev@redneboa.es>
#                       SerpentCS
#
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


class HotelReservation(models.Model):

    @api.multi
    def _generate_color(self):
        self.ensure_one()
        now_utc_dt = date_utils.now()
        diff_checkin_now = date_utils.date_diff(now_utc_dt, self.checkin,
                                                hours=False)
        diff_checkout_now = date_utils.date_diff(now_utc_dt, self.checkout,
                                                 hours=False)

        ir_values_obj = self.env['ir.values']
        reserv_color = '#FFFFFF'
        reserv_color_text = '#000000'
        if self.reservation_type == 'staff':
            reserv_color = ir_values_obj.get_default('hotel.config.settings',
                                                     'color_staff')
            reserv_color_text = ir_values_obj.get_default(
                'hotel.config.settings',
                'color_letter_staff')
        elif self.reservation_type == 'out':
            reserv_color = ir_values_obj.get_default('hotel.config.settings',
                                                     'color_dontsell')
            reserv_color_text = ir_values_obj.get_default(
                'hotel.config.settings',
                'color_letter_dontsell')
        elif self.to_assign:
            reserv_color = ir_values_obj.get_default('hotel.config.settings',
                                                     'color_to_assign')
            reserv_color_text = ir_values_obj.get_default(
                'hotel.config.settings',
                'color_letter_to_assign')
        elif self.state == 'draft':
            reserv_color = ir_values_obj.get_default('hotel.config.settings',
                                                     'color_pre_reservation')
            reserv_color_text = ir_values_obj.get_default(
                'hotel.config.settings',
                'color_letter_pre_reservation')
        elif self.state == 'confirm':
            if self.folio_id.invoices_amount == 0:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_reservation_pay')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_reservation_pay')
            else:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_reservation')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_reservation')
        elif self.state == 'booking':
            if self.folio_id.invoices_amount == 0:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_stay_pay')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_stay_pay')
            else:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_stay')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_stay')
        else:
            if self.folio_id.invoices_amount == 0:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_checkout')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_checkout')
            else:
                reserv_color = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_payment_pending')
                reserv_color_text = ir_values_obj.get_default(
                    'hotel.config.settings', 'color_letter_payment_pending')
        return (reserv_color, reserv_color_text)

    @api.depends('state', 'reservation_type', 'folio_id.invoices_amount')
    def _compute_color(self):
        _logger.info('_compute_color')
        for rec in self:
            colors = rec._generate_color()
            rec.update({
                'reserve_color': colors[0],
                'reserve_color_text': colors[1],
            })
            rec.folio_id.color = colors[0]

            # hotel_reserv_obj = self.env['hotel.reservation']
            # if rec.splitted:
            #     master_reservation = rec.parent_reservation or rec
            #     splitted_reservs = hotel_reserv_obj.search([
            #         ('splitted', '=', True),
            #         '|', ('parent_reservation', '=', master_reservation.id),
            #              ('id', '=', master_reservation.id),
            #         ('folio_id', '=', rec.folio_id.id),
            #         ('id', '!=', rec.id),
            #     ])
            #     splitted_reservs.write({'reserve_color': rec.reserve_color})

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''

        return super(HotelReservation, self).copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._amount_line(field_name, arg)

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._number_packages(field_name, arg)

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

    # @api.constrains('checkin', 'checkout') #Why dont run api.depends?¿?
    # def _computed_nights(self):
    #     for res in self:
    #         if res.checkin and res.checkout:
    #             nights = days_diff = date_utils.date_diff(
    #                 self.checkin,
    #                 self.checkout, hours=False)
    #         res.nights = nights

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += [
                '|',
                ('folio_id.name', operator, name),
                ('product_id.name', operator, name)
            ]
        return super(HotelReservation, self).name_search(
            name='', args=args, operator='ilike', limit=limit)

    @api.multi
    def name_get(self):
        result = []
        for res in self:
            name = u'%s (%s)' % (res.folio_id.name, res.product_id.name)
            result.append((res.id, name))
        return result

    _name = 'hotel.reservation'
    _description = 'hotel reservation'
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    _order = "last_updated_res desc, name"

    _defaults = {
        'product_id': False
    }

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    adults = fields.Integer('Adults', size=64, readonly=False,
                            track_visibility='always',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children', size=64, readonly=False,
                              track_visibility='always',
                              help='Number of children there in guest list.')
    to_assign = fields.Boolean('To Assign')
    state = fields.Selection([('draft', 'Pre-reservation'), ('confirm', 'Pending Entry'),
                              ('booking', 'On Board'), ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='always')
    reservation_type = fields.Selection(related='folio_id.reservation_type',
                                        default=lambda *a: 'normal')
    cancelled_reason = fields.Selection([
        ('late', 'Late'),
        ('intime', 'In time'),
        ('noshow', 'No Show')], 'Cause of cancelled')
    out_service_description = fields.Text('Cause of out of service')
    order_line_id = fields.Many2one('sale.order.line', string='Order Line',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', string='Folio',
                               ondelete='cascade')
    folio_name = fields.Char(compute="_computed_folio_name")
    checkin = fields.Datetime('Check In', required=True,
                              default=_get_default_checkin,
                              track_visibility='always')
    checkout = fields.Datetime('Check Out', required=True,
                               default=_get_default_checkout,
                               track_visibility='always')
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type')
    virtual_room_id = fields.Many2one('hotel.virtual.room',
                                      string='Virtual Room Type',
                                      required=True)
    partner_id = fields.Many2one(related='folio_id.partner_id')
    reservation_lines = fields.One2many('hotel.reservation.line',
                                        'reservation_id',
                                        readonly=True,
                                        states={
                                            'draft': [('readonly', False)],
                                            'sent': [('readonly', False)],
                                            'confirm': [('readonly', False)],
                                            'booking': [('readonly', False)],
                                        })
    reserve_color = fields.Char(compute='_compute_color', string='Color',
                                store=True)
    reserve_color_text = fields.Char(compute='_compute_color', string='Color',
                                     store=True)
    service_line_ids = fields.One2many('hotel.service.line', 'ser_room_line')
    pricelist_id = fields.Many2one('product.pricelist',
                                   related='folio_id.pricelist_id',
                                   readonly="1")
    cardex_ids = fields.One2many('cardex', 'reservation_id')
    # TODO: As cardex_count is a computed field, it can't not be used in a domain filer
    # Non-stored field hotel.reservation.cardex_count cannot be searched
    # searching on a computed field can also be enabled by setting the search parameter.
    # The value is a method name returning a Domains
    cardex_count = fields.Integer('Cardex counter',
                                  compute='_compute_cardex_count')
    cardex_pending = fields.Boolean('Cardex Pending',
                                    compute='_compute_cardex_count', search='_search_cardex_pending')
    cardex_pending_num = fields.Integer('Cardex Pending Num',
                                        compute='_compute_cardex_count')
    check_rooms = fields.Boolean('Check Rooms')
    is_checkin = fields.Boolean()
    is_checkout = fields.Boolean()
    splitted = fields.Boolean('Splitted', default=False)
    parent_reservation = fields.Many2one('hotel.reservation',
                                         'Parent Reservation')
    overbooking = fields.Boolean('Is Overbooking', default=False)
    # To show de total amount line in read_only mode
    amount_reservation = fields.Float('Total',
                                      compute='_computed_amount_reservation')
    amount_reservation_services = fields.Float('Services Amount',
                                               compute='_computed_amount_reservation')
    amount_room = fields.Float('Amount Room', compute="_computed_amount_reservation")
    amount_discount = fields.Float('Room with Discount', compute="_computed_amount_reservation")
    discount_type = fields.Selection([
        ('percent', 'Percent'),
        ('fixed', 'Fixed')], 'Discount Type', default=lambda *a: 'percent')
    discount_fixed = fields.Float('Fixed Discount')
    edit_room = fields.Boolean(default=True)
    nights = fields.Integer('Nights',compute='_computed_nights', store=True)
    channel_type = fields.Selection(related='folio_id.channel_type')
    last_updated_res = fields.Datetime('Last Updated')
    folio_pending_amount = fields.Monetary(related='folio_id.invoices_amount')
    segmentation_id = fields.Many2many(related='folio_id.segmentation_id')
    shared_folio = fields.Boolean (compute='_computed_shared')
    #Used to notify is the reservation folio has other reservations or services
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    phone = fields.Char('Phone', related='partner_id.phone')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')
    folio_internal_comment = fields.Text(string='Internal Folio Notes',
                                           related='folio_id.internal_comment')
    preconfirm = fields.Boolean('Auto confirm to Save', default=True)
    
    def _computed_folio_name(self):
        for res in self:
            res.folio_name = res.folio_id.name + '-' + \
                res.folio_id.date_order

    @api.multi
    def action_checks(self):
        self.ensure_one()
        return {
            'name': _('Cardexs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cardex',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', '=', self.id)],
            'target': 'new',
        }

    @api.multi
    def _computed_shared(self):
        for record in self:
            if record.folio_id:
                if len(record.folio_id.room_lines) > 1 or \
                        record.folio_id.service_lines.filtered(lambda x: (
                        x.ser_room_line != record.id)):
                    record.shared_folio = True
                else:
                    record.shared_folio = False
                
    @api.depends('checkin', 'checkout')
    def _computed_nights(self):
        for res in self:
            if res.checkin and res.checkout:
                nights = days_diff = date_utils.date_diff(
                    res.checkin,
                    res.checkout, hours=False)
                res.nights = nights

    @api.depends('reservation_lines', 'discount_fixed', 'discount')
    def _computed_amount_reservation(self):
        _logger.info('_computed_amount_reservation')
        for res in self:
            amount_reservation = amount_service = amount_room = 0
            for line in res.reservation_lines:
                amount_room += line.price
            for service in res.service_line_ids:
                # We must calc the line to can show the price in edit mode
                # on smartbutton whithout having to wait to save.
                total_line = service.price_unit * service.product_uom_qty
                discount = (service.discount * total_line) / 100
                amount_service += total_line - discount            
            res.amount_room = amount_room #To view price_unit with read_only
            if res.discount_type == 'fixed':
                res.discount = (res.discount_fixed * 100) / amount_room
            else:
                res.discount_fixed = (res.discount * amount_room) / 100      
            res.amount_discount = amount_room - res.discount_fixed
            res.price_unit = res.amount_room
            res.amount_reservation_services = amount_service
            res.amount_reservation = res.amount_discount + amount_service #To the smartbutton

    @api.multi
    def _compute_cardex_count(self):
        _logger.info('_compute_cardex_count')
        for res in self:
            res.cardex_count = len(res.cardex_ids)
            res.cardex_pending_num = (res.adults + res.children) \
                - len(res.cardex_ids)
            if (res.adults + res.children - len(res.cardex_ids)) <= 0:
                res.cardex_pending = False
            else:
                res.cardex_pending = True

    # https://www.odoo.com/es_ES/forum/ayuda-1/question/calculated-fields-in-search-filter-possible-118501
    @api.multi
    def _search_cardex_pending(self, operator, value):
        recs = self.search([]).filtered(lambda x: x.cardex_pending is True)
        if recs:
            return [('id', 'in', [x.id for x in recs])]

    @api.multi
    def action_pay_folio(self):
        self.ensure_one()
        return self.folio_id.action_pay()

    @api.multi
    def action_pay_reservation(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = min(self.amount_reservation, self.folio_pending_amount)
        view_id = self.env.ref('hotel.view_account_payment_folio_form').id
        return{
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': {
                'default_folio_id': self.folio_id.id,
                'default_room_id': self.id,
                'default_amount': amount,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': partner,
                'default_communication': self.name,
            },
            'target': 'new',
        }

    @api.model
    def daily_plan(self):
        _logger.info('daily_plan')
        today_utc_dt = date_utils.now()
        yesterday_utc_dt = today_utc_dt - timedelta(days=1)
        hotel_tz = self.env['ir.values'].get_default('hotel.config.settings',
                                                     'tz_hotel')
        today_dt = date_utils.dt_as_timezone(today_utc_dt, hotel_tz)
        yesterday_dt = date_utils.dt_as_timezone(yesterday_utc_dt, hotel_tz)

        today_str = today_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        yesterday_str = yesterday_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        reservations_to_checkout = self.env['hotel.reservation'].search([
            ('state', 'not in', ['done']),
            ('checkout', '<', today_str)
            ])
        for res in reservations_to_checkout:
            res.action_reservation_checkout()

        reservations = self.env['hotel.reservation'].search([
            ('reservation_lines.date', 'in', [today_str,
                                              yesterday_str]),
            ('state', 'in', ['confirm', 'booking'])
        ])
        self._cr.execute("update hotel_reservation set is_checkin = False, \
                            is_checkout = False where is_checkin = True or \
                            is_checkout = True")
        checkins_res = reservations.filtered(lambda x: (
            x.state in ('confirm','draft')
            and date_utils.date_compare(x.checkin, today_str, hours=False)
            and x.reservation_type == 'normal'))
        checkins_res.write({'is_checkin': True})
        checkouts_res = reservations.filtered(lambda x: (
            x.state not in ('done','cancelled')
            and date_utils.date_compare(x.checkout, today_str,
                                        hours=False)
            and x.reservation_type == 'normal'))
        checkouts_res.write({'is_checkout': True})
        self.env['hotel.folio'].daily_plan()
        return True

    @api.model
    def checkin_is_today(self):
        self.ensure_one()
        date_now_str = date_utils.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        return date_utils.date_compare(self.checkin, date_now_str, hours=False)

    @api.model
    def checkout_is_today(self):
        self.ensure_one()
        date_now_str = date_utils.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        return date_utils.date_compare(self.checkout, date_now_str,
                                       hours=False)

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled',
                'to_assign': False,
                'discount': 100.0,
            })
            if record.checkin_is_today:
                record.is_checkin = False
                folio = self.env['hotel.folio'].browse(record.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id),
                    ('is_checkin', '=', True)
                ])

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'cancelled')
                ])
                splitted_reservs.action_cancel()

    @api.multi
    def draft(self):
        for record in self:
            record.write({'state': 'draft', 'to_assign': False})

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'draft')
                ])
                splitted_reservs.draft()

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            record.state = 'done'
            record.to_assign = False
            if record.checkout_is_today():
                record.is_checkout = False
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkouts_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id),
                    ('is_checkout', '=', True)
                ])

    @api.multi
    def overbooking_button(self):
        self.ensure_one()
        return self.write({'overbooking': not self.overbooking})
    
    @api.multi
    def open_master(self):
        self.ensure_one()
        if not self.parent_reservation:
            raise ValidationError(_("This is the parent reservation"))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'views': [[False, "form"]],
            'target': 'new',
            'res_id': self.parent_reservation.id,
        }

    @api.multi
    def open_folio(self):
        action = self.env.ref('hotel.open_hotel_folio1_form_tree_all').read()[0]
        if self.folio_id:
            action['views'] = [(self.env.ref('hotel.view_hotel_folio1_form').id, 'form')]
            action['res_id'] = self.folio_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def open_reservation_form(self):
        action = self.env.ref('hotel.open_hotel_reservation_form_tree_all').read()[0]        
        action['views'] = [(self.env.ref('hotel.view_hotel_reservation_form').id, 'form')]
        action['res_id'] = self.id
        return action
        
    @api.multi
    def unify(self):
        self.ensure_one()
        if not self.splitted:
            raise ValidationError(_("This reservation can't be unified"))

        master_reservation = self.parent_reservation or self
        self_is_master = (master_reservation == self)

        splitted_reservs = self.env['hotel.reservation'].search([
            ('splitted', '=', True),
            ('folio_id', '=', self.folio_id.id),
            '|',
            ('parent_reservation', '=', master_reservation.id),
            ('id', '=', master_reservation.id)
        ])

        rooms_products = splitted_reservs.mapped('product_id.id')
        if len(rooms_products) > 1 or \
                (len(rooms_products) == 1
                    and master_reservation.product_id.id != rooms_products[0]):
            raise ValidationError(_("This reservation can't be unified: They \
                                    all need to be in the same room"))

        # Search checkout
        last_checkout = splitted_reservs[0].checkout
        for reserv in splitted_reservs:
            if last_checkout < reserv.checkout:
                last_checkout = reserv.checkout

        # Agrupate reservation lines
        reservation_lines = splitted_reservs.mapped('reservation_lines')
        reservation_lines.sorted(key=lambda r: r.date)
        rlines = [(5, False, False)]
        tprice = 0.0
        for rline in reservation_lines:
            rlines.append((0, False, {
                'date': rline.date,
                'price': rline.price,
            }))
            tprice += rline.price

        # Unify
        folio = self.folio_id   # FIX: To Allow Unify confirm reservations
        state = folio.state     # FIX
        folio.state = 'draft'   # FIX
        osplitted_reservs = splitted_reservs - master_reservation
        osplitted_reservs.sudo().unlink()
        folio.state = state  # FIX

        # FIXME: Two writes because checkout regenerate reservation lines
        master_reservation.write({
            'checkout': last_checkout,
            'splitted': False,
        })
        master_reservation.write({
            'reservation_lines': rlines,
            'unit_price': tprice,
        })

        if not self_is_master:
            return {'type': 'ir.actions.act_window_close'}
        return True

    '''
          Created this because "copy()" function create a new record
        and collide with date restrictions.
        This function generate a usable dictionary with reservation values
        for copy purposes.
    '''
    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        return {
            'name': self.name,
            'adults': self.adults,
            'children': self.children,
            'checkin': checkin or self.checkin,
            'checkout': checkout or self.checkout,
            'folio_id': self.folio_id.id,
            'product_id': self.product_id.id,
            'parent_reservation': self.parent_reservation.id,
            'state': self.state,
            'overbooking': self.overbooking,
            'price_unit': self.price_unit,
            'splitted': self.splitted,
            'virtual_room_id': self.virtual_room_id.id,
        }

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        if not 'reservation_type' in vals or not vals.get('reservation_type'):
            vals.update({'reservation_type': 'normal'})
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        elif 'partner_id' in vals:
            folio_vals = {'partner_id':int(vals.get('partner_id')),
                          'channel_type': vals.get('channel_type')}
            folio = self.env["hotel.folio"].create(folio_vals)
            vals.update({'order_id': folio.order_id.id,
                         'folio_id': folio.id,
                         'reservation_type': vals.get('reservation_type'),
                         'channel_type': vals.get('channel_type')})
        vals.update({
            'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })
        if folio:
            record = super(HotelReservation, self).create(vals)
            # Check Capacity
            room = self.env['hotel.room'].search([
                ('product_id', '=', record.product_id.id)
            ])
            persons = record.adults + record.children
            if persons > room.capacity:
                raise ValidationError(
                    _("Reservation persons can't be higher than room capacity"))
            if record.adults == 0:
                raise ValidationError(_("Reservation has no adults"))
            if (record.state == 'draft' and record.folio_id.state == 'sale') or \
                    record.preconfirm == True:
                record.confirm()
            record._compute_color()

            # Update Availability (Removed because wubook-proto do it)
            # cavail = self.env['hotel.reservation'].get_availability(
            #     record.checkin,
            #     record.checkout,
            #     record.product_id.id, dbchanged=False)
            # hotel_vroom_avail_obj = self.env['hotel.virtual.room.availability']
            # for item in cavail:
            #     for rec in item['days']:
            #         vroom_avail = hotel_vroom_avail_obj.search([
            #             ('virtual_room_id', '=', item['id']),
            #             ('date', '=', rec['date'])
            #         ])
            #         vals = {
            #             'avail': rec['avail']
            #         }
            #         if vroom_avail:
            #             vroom_avail.write(vals)
            #         else:
            #             vals.update({
            #                 'virtual_room_id': item['id'],
            #                 'date': rec['date'],
            #             })
            #             hotel_vroom_avail_obj.create(vals)

            return record

    @api.multi
    def write(self, vals):
        pricesChanged = ('checkin' in vals or 'checkout' in vals or 'discount' in vals)           
        vals.update({
            'edit_room': False,
        })
        if pricesChanged or 'state' in vals or 'virtual_room_id' in vals:
            vals.update({
            'last_updated_res': date_utils.now(hours=True).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })
        res = super(HotelReservation, self).write(vals)
        if pricesChanged:
            for record in self:
                if record.reservation_type in ('staff', 'out'):
                    record.update({'price_unit': 0})
                record.folio_id.compute_invoices_amount()       
        for record in self:
            if (pricesChanged and 'reservation_lines' not in vals) and \
                    not record.reservation_lines: #To allow add tree edit bottom room_lines on folio form
                checkin = vals.get('checkin', record.checkin)
                checkout = vals.get('checkout', record.checkout)
                days_diff = date_utils.date_diff(checkin,
                                                 checkout, hours=False)                                                 
                rlines = record.prepare_reservation_lines(checkin, days_diff)
                record.update({
                    'reservation_lines': rlines['commands']
                })
        return res

    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            line.uos_change(product_uos, product_uos_qty=0,
                            product_id=None)
        return True

    @api.onchange('adults', 'children', 'product_id')
    def check_capacity(self):
        if self.product_id:
            room = self.env['hotel.room'].search([
                ('product_id', '=', self.product_id.id)
            ])
            persons = self.adults + self.children
            if room.capacity < persons:
                self.adults = room.capacity
                self.children = 0
                raise UserError(
                    _('%s people do not fit in this room! ;)') % (persons))

    @api.onchange('virtual_room_id')
    def on_change_virtual_room_id(self):
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        days_diff = date_utils.date_diff(
                                self.checkin, self.checkout, hours=False)
        rlines = self.prepare_reservation_lines(
            self.checkin,
            days_diff,
            update_old_prices=True)
        self.reservation_lines = rlines['commands']

        if self.reservation_type in ['staff', 'out']:
            self.price_unit = 0.0
            self.cardex_pending = 0
        else:
            self.price_unit = rlines['total_price']

    @api.onchange('checkin', 'checkout', 'product_id', 'reservation_type', 'virtual_room_id')
    def on_change_checkin_checkout_product_id(self):
        _logger.info('on_change_checkin_checkout_product_id')
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if self.product_id:
            room = self.env['hotel.room'].search([
                ('product_id', '=', self.product_id.id)
            ])
            if self.adults == 0:
                self.adults = room.capacity
            if not self.virtual_room_id and room.price_virtual_room:
                self.virtual_room_id = room.price_virtual_room.id

        # UTC -> Hotel tz
        tz = self.env['ir.values'].get_default('hotel.config.settings',
                                               'tz_hotel')
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)

        if self.virtual_room_id:
            checkin_str = chkin_utc_dt.strftime('%d/%m/%Y')
            checkout_str = chkout_utc_dt.strftime('%d/%m/%Y')
            self.name = self.virtual_room_id.name + ': ' + checkin_str + ' - '\
                + checkout_str
            self.product_uom = self.product_id.uom_id

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

        if self.state == 'confirm' and self.checkin_is_today():
                self.is_checkin = True
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                if folio:
                    folio.checkins_reservations = folio.room_lines.search_count([
                        ('folio_id', '=', folio.id), ('is_checkin', '=', True)
                    ])

        if self.state == 'booking' and self.checkout_is_today():
                self.is_checkout = False
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                if folio:
                    folio.checkouts_reservations = folio.room_lines.search_count([
                        ('folio_id', '=', folio.id), ('is_checkout', '=', True)
                    ])

        days_diff = date_utils.date_diff(
                                self.checkin, self.checkout, hours=False)
        rlines = self.prepare_reservation_lines(
            self.checkin,
            days_diff,
            update_old_prices=False)
        self.reservation_lines = rlines['commands']

        if self.reservation_type in ['staff', 'out']:
            self.price_unit = 0.0
            self.cardex_pending = 0
        else:
            self.price_unit = rlines['total_price']


    @api.model
    def get_availability(self, checkin, checkout, product_id, dbchanged=True,
                         dtformat=DEFAULT_SERVER_DATE_FORMAT):
        date_start = date_utils.get_datetime(checkin)
        date_end = date_utils.get_datetime(checkout)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(date_start, date_end, hours=False)

        hotel_vroom_obj = self.env['hotel.virtual.room']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']

        rooms_avail = []
        vrooms = hotel_vroom_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for vroom in vrooms:
            rdays = []
            for i in range(0, date_diff):
                ndate_dt = date_start + timedelta(days=i)
                ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                avail = len(hotel_vroom_obj.check_availability_virtual_room(
                    ndate_str,
                    ndate_str,
                    virtual_room_id=vroom.id))
                if not dbchanged:
                    avail = avail - 1
                # Can be less than zero because 'avail' can not equal
                # with the real 'avail' (ex. Online Limits)
                avail = max(min(avail, vroom.total_rooms_count), 0)
                rdays.append({
                    'date': ndate_dt.strftime(dtformat),
                    'avail': avail,
                })
            ravail = {'id': vroom.id, 'days': rdays}
            rooms_avail.append(ravail)

        return rooms_avail

    @api.multi
    def prepare_reservation_lines(self, str_start_date_utc, days,
                                  update_old_prices=False):
        self.ensure_one()
        total_price = 0.0
        cmds = [(5, False, False)]
        # TO-DO: Redesign relation between hotel.reservation
        # and sale.order.line to allow manage days by units in order
        #~ if self.invoice_status == 'invoiced' and not self.splitted:
            #~ raise ValidationError(_("This reservation is already invoiced. \
                        #~ To expand it you must create a new reservation."))
        hotel_tz = self.env['ir.values'].sudo().get_default(
            'hotel.config.settings', 'hotel_tz')
        start_date_utc_dt = date_utils.get_datetime(str_start_date_utc)
        start_date_dt = date_utils.dt_as_timezone(start_date_utc_dt, hotel_tz)

        room = self.env['hotel.room'].search([
            ('product_id', '=', self.product_id.id)
        ])
        product_id = self.virtual_room_id \
            or room.sale_price_type == 'vroom' \
            and room.price_virtual_room.product_id \
            or self.product_id
        pricelist_id = self.env['ir.values'].sudo().get_default(
            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        old_lines_ids = self.mapped('reservation_lines.id')
        for i in range(0, days):
            ndate = start_date_dt + timedelta(days=i)
            ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
            prod = product_id.with_context(
                lang=self.partner_id.lang,
                partner=self.partner_id.id,
                quantity=1,
                date=ndate_str,
                pricelist=pricelist_id,
                uom=self.product_uom.id)
            if not self.reservation_lines.ids or \
                ndate_str not in self.mapped('reservation_lines.date') or \
                    update_old_prices:
                line_price = prod.price
                cmds.append((0, False, {
                    'date': ndate_str,
                    'price': line_price
                }))
            else:
                line = self.reservation_lines.search([
                    ('id', 'in', old_lines_ids),
                    ('date', '=', ndate)])
                line_price = line.price
                cmds.append((0, False, {
                        'date': ndate_str,
                        'price': line_price
                    }))
            total_price += line_price
        if self.adults == 0 and self.product_id:
            room = self.env['hotel.room'].search([
                ('product_id', '=', self.product_id.id)
            ])
            self.adults = room.capacity
        return {'total_price': total_price, 'commands': cmds}

    @api.multi
    @api.onchange('checkin', 'checkout', 'room_type_id', 'virtual_room_id',
                  'check_rooms', 'edit_room', 'product_id')
    def on_change_checkout(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('on_change_checkout')
        self.ensure_one()
        now_utc_dt = date_utils.now()
        if not self.checkin:
            self.checkin = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            now_utc_dt = date_utils.get_datetime(self.checkin)\
                + timedelta(days=1)
            self.checkout = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.overbooking:
            return
        checkout_dt = date_utils.get_datetime(self.checkout)
        # Reservation end day count as free day. Not check it
        checkout_dt -= timedelta(days=1)
        occupied = self.env['hotel.reservation'].occupied(
            self.checkin,
            checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)).filtered(
                lambda r: r.id != self._origin.id)
        rooms_occupied = occupied.mapped('product_id.id')
        if self.product_id and self.product_id.id in rooms_occupied:
            warning_msg = _('You tried to change \
                   reservation with room those already reserved in this \
                   reservation period')
            raise ValidationError(warning_msg)
        domain_rooms = [
            ('isroom', '=', True),
            ('id', 'not in', rooms_occupied)
        ]
        if self.check_rooms:
            if self.room_type_id:
                domain_rooms.append(
                    ('categ_id.id', '=', self.room_type_id.cat_id.id)
                )
            if self.virtual_room_id:
                room_categories = self.virtual_room_id.room_type_ids.mapped(
                    'cat_id.id')
                link_virtual_rooms = self.virtual_room_id.room_ids\
                    | self.env['hotel.room'].search([
                        ('categ_id.id', 'in', room_categories)])
                room_ids = link_virtual_rooms.mapped('product_id.id')
                domain_rooms.append(('id', 'in', room_ids))
        return {'domain': {'product_id': domain_rooms}}

    @api.multi
    def confirm(self):
        '''
        @param self: object pointer
        '''
        _logger.info('confirm')
        hotel_folio_obj = self.env['hotel.folio']
        hotel_reserv_obj = self.env['hotel.reservation']
        for r in self:
            vals = {}
            if r.cardex_ids:
                vals.update({'state': 'booking', 'to_assign': False})
            else:
                vals.update({'state': 'confirm', 'to_assign': False})
            if r.checkin_is_today():
                vals.update({'is_checkin': True})
                folio = hotel_folio_obj.browse(r.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([
                    ('folio_id', '=', folio.id), ('is_checkin', '=', True)])
            r.write(vals)

            if r.splitted:
                master_reservation = r.parent_reservation or r
                splitted_reservs = hotel_reserv_obj.search([
                    ('splitted', '=', True),
                    '|', ('parent_reservation', '=', master_reservation.id),
                         ('id', '=', master_reservation.id),
                    ('folio_id', '=', r.folio_id.id),
                    ('id', '!=', r.id),
                    ('state', '!=', 'confirm')
                ])
                splitted_reservs.confirm()
        return True

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        for res in self:
            res.action_reservation_checkout()
        return True

    @api.one
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        line_id = self.order_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)

    @api.constrains('checkin', 'checkout', 'state', 'product_id')
    def check_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        chkin_utc_dt = date_utils.get_datetime(self.checkin)
        chkout_utc_dt = date_utils.get_datetime(self.checkout)
        if chkin_utc_dt >= chkout_utc_dt:
                raise ValidationError(_('Room line Check In Date Should be \
                less than the Check Out Date!'))
        if not self.overbooking and not self._context.get("ignore_avail_restrictions", False):
            # Reservation end day count as free day. Not check it
            chkout_utc_dt -= timedelta(days=1)
            occupied = self.env['hotel.reservation'].occupied(
                self.checkin,
                chkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            occupied = occupied.filtered(
                lambda r: r.product_id.id == self.product_id.id
                and r.id != self.id)
            occupied_name = ','.join(str(x.folio_id.name) for x in occupied)
            if occupied:
                warning_msg = _('You tried to change/confirm \
                   reservation with room those already reserved in this \
                   reservation period: %s') % occupied_name
                raise ValidationError(warning_msg)

    @api.multi
    def unlink(self):
        for record in self:
            record.order_line_id.unlink()
        return super(HotelReservation, self).unlink()

    @api.model
    def occupied(self, str_checkin_utc, str_checkout_utc):
        """
        Return a RESERVATIONS array between in and out parameters
        IMPORTANT: This function should receive the dates in UTC datetime zone,
                    as String format
        """
        tz_hotel = self.env['ir.values'].sudo().get_default(
                                        'hotel.config.settings', 'tz_hotel')
        checkin_utc_dt = date_utils.get_datetime(str_checkin_utc)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt, tz_hotel)
        days_diff = date_utils.date_diff(str_checkin_utc, str_checkout_utc,
                                         hours=False)
        dates_list = date_utils.generate_dates_list(checkin_dt, days_diff,
                                                    stz=tz_hotel)
        reservations = self.env['hotel.reservation'].search([
            ('reservation_lines.date', 'in', dates_list),
            ('state', '!=', 'cancelled'),
            ('overbooking', '=', False)
        ])
        return reservations

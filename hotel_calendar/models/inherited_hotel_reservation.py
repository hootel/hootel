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
from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from odoo.addons.hotel import date_utils
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.model
    def _hcalendar_reservation_data(self, reservations):
        json_reservations = []
        json_reservation_tooltips = {}
        for reserv in reservations:
            json_reservations.append((
                reserv.product_id.id,
                reserv.id,
                reserv.folio_id.partner_id.name,
                reserv.adults,
                reserv.children,
                reserv.checkin,
                reserv.checkout,
                reserv.folio_id.id,
                reserv.reserve_color,
                reserv.splitted,
                reserv.parent_reservation.id,
                False,  # Read-Only
                reserv.splitted,   # Fix Days
                False))  # Fix Rooms
            num_split = 0
            if reserv.splitted:
                master_reserv = reserv.parent_reservation or reserv
                num_split = self.search_count([
                    ('folio_id', '=', reserv.folio_id.id),
                    '|', ('parent_reservation', '=', master_reserv.id),
                         ('id', '=', master_reserv.id),
                    ('splitted', '=', True),
                ])
            json_reservation_tooltips.update({
                reserv.id: (
                    reserv.folio_id.partner_id.name,
                    reserv.folio_id.partner_id.mobile or
                    reserv.folio_id.partner_id.phone or _('Undefined'),
                    reserv.checkin,
                    num_split)
            })
        return (json_reservations, json_reservation_tooltips)

    @api.model
    def _hcalendar_room_data(self, rooms):
        pricelist_id = self.env['ir.values'].sudo().get_default(
                            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        json_rooms = []
        room_type_obj = self.env['hotel.room.type']
        vroom_obj = self.env['hotel.virtual.room']
        for room in rooms:
            room_type = room_type_obj.search([
                ('cat_id', '=', room.categ_id.id)
            ], limit=1)
            vrooms = vroom_obj.search([
                '|', ('room_ids', 'in', room.id),
                     ('room_type_ids.id', '=', room.categ_id.id)])
            json_rooms.append((
                room.product_id.id,
                room.name,
                room.capacity,
                room.categ_id.id,
                room_type.code_type,
                room.shared_room,
                room.uom_id.id,
                room.sale_price_type == 'vroom'
                and ['pricelist', room.price_virtual_room.id, pricelist_id]
                or ['fixed', room.list_price],
                room.sale_price_type == 'vroom'
                and room.price_virtual_room.name
                or 'Fixed Price',
                vrooms.mapped('name')))
        return json_rooms

    @api.multi
    def get_hcalendar_reservations_data(self, dfrom, dto, domain, rooms):
        domain = domain or []
        date_start = date_utils.get_datetime(dfrom, hours=False) \
            - timedelta(days=1)
        date_end = date_utils.get_datetime(dto, end_day=True)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_end_str = date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        room_product_ids = rooms.mapped('product_id.id')
        domain.insert(0, ('product_id', 'in', room_product_ids))
        domain.insert(0, ('state', 'in', ['draft',
                                          'confirm',
                                          'booking',
                                          'done',
                                          False]))
        reservations_raw = self.env['hotel.reservation'].search(
            domain,
            order="checkin DESC, checkout ASC, adults DESC, children DESC")
        reservations_ll = self.env['hotel.reservation'].search([
            ('checkin', '<=', date_end_str),
            ('checkout', '>=', date_start_str)
        ])
        reservations_lr = self.env['hotel.reservation'].search([
            ('checkin', '>=', date_start_str),
            ('checkout', '<=', date_end_str)
        ])
        reservations = (reservations_ll | reservations_lr) & reservations_raw
        return self._hcalendar_reservation_data(reservations)

    @api.multi
    def get_hcalendar_pricelist_data(self, dfrom, dto):
        pricelist_id = self.env['ir.values'].sudo().get_default(
                            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        date_start = date_utils.get_datetime(dfrom, hours=False) \
            - timedelta(days=1)
        date_diff = date_utils.date_diff(date_start, dto, hours=False) + 1
        # Get Prices
        json_rooms_prices = {pricelist_id: []}
        vrooms = self.env['hotel.virtual.room'].search([])
        vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']

        for vroom in vrooms:
            days = {}
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                prod_price_id = vroom_pr_cached_obj.search([
                    ('virtual_room_id', '=', vroom.id),
                    ('date', '=', ndate_str)
                ], limit=1)
                days.update({
                    ndate.strftime("%d/%m/%Y"): prod_price_id and
                    prod_price_id.price or vroom.product_id.with_context(
                        quantity=1,
                        date=ndate_str,
                        pricelist=pricelist_id).price
                })
            json_rooms_prices[pricelist_id].append({
                'room': vroom.id,
                'days': days,
                'title': vroom.name,
            })
        return json_rooms_prices

    @api.multi
    def get_hcalendar_restrictions_data(self, dfrom, dto):
        restriction_id = self.env['ir.values'].sudo().get_default(
                            'hotel.config.settings', 'parity_restrictions_id')
        if restriction_id:
            restriction_id = int(restriction_id)
        date_start = date_utils.get_datetime(dfrom, hours=False) \
            - timedelta(days=1)
        date_diff = date_utils.date_diff(dfrom, dto, hours=False) + 1
        # Get Prices
        json_rooms_rests = {}
        vrooms = self.env['hotel.virtual.room'].search([])
        vroom_rest_obj = self.env['hotel.virtual.room.restriction.item']
        for vroom in vrooms:
            days = {}
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                rest_id = vroom_rest_obj.search([
                    ('virtual_room_id', '=', vroom.id),
                    ('date_start', '>=', ndate_str),
                    ('date_end', '<=', ndate_str),
                    ('applied_on', '=', '0_virtual_room')
                ], limit=1)
                if rest_id:
                    days.update({
                        ndate.strftime("%d/%m/%Y"): (
                            rest_id.min_stay,
                            rest_id.min_stay_arrival,
                            rest_id.max_stay,
                            rest_id.closed,
                            rest_id.closed_arrival,
                            rest_id.closed_departure)
                    })
            json_rooms_rests.update({vroom.id: days})
        return json_rooms_rests

    @api.multi
    def get_hcalendar_settings(self):
        type_move = self.env['ir.values'].get_default(
                                        'hotel.config.settings', 'type_move')
        user_id = self.env['res.users'].browse(self.env.uid)
        return {
            'divide_rooms_by_capacity': self.env['ir.values'].get_default(
                    'hotel.config.settings', 'divide_rooms_by_capacity'),
            'eday_week': self.env['ir.values'].get_default(
                        'hotel.config.settings', 'end_day_week'),
            'days': self.env['ir.values'].get_default(
                    'hotel.config.settings', 'default_num_days') or 'month',
            'allow_invalid_actions': type_move == 'allow_invalid',
            'assisted_movement': type_move == 'assisted',
            'default_arrival_hour': self.env['ir.values'].get_default(
                    'hotel.config.settings', 'default_arrival_hour'),
            'default_departure_hour': self.env['ir.values'].get_default(
                    'hotel.config.settings', 'default_departure_hour'),
            'show_notifications': user_id.pms_show_notifications,
        }

    @api.multi
    def get_hcalendar_all_data(self, dfrom, dto, domainRooms,
                               domainReservations, withRooms=True,
                               withPricelist=True, withRestrictions=True):
        if not dfrom or not dto:
            raise ValidationError(_('Input Error: No dates defined!'))

        domainRooms = domainRooms or []
        domainReservations = domainReservations or []

        rooms = self.env['hotel.room'].search(domainRooms)
        json_res, json_res_tooltips = self.get_hcalendar_reservations_data(
            dfrom, dto, domainReservations, rooms)

        json_prices = {}
        if withPricelist:
            json_prices = self.get_hcalendar_pricelist_data(dfrom, dto)
        json_restr = {}
        if withRestrictions:
            json_restr = self.get_hcalendar_restrictions_data(dfrom, dto)

        vals = {
            'rooms': withRooms and self._hcalendar_room_data(rooms) or [],
            'reservations': json_res,
            'tooltips': json_res_tooltips,
            'pricelist': json_prices,
            'restrictions': json_restr,
        }

        return vals

    @api.multi
    def send_bus_notification(self, naction, ntype, ntitle=''):
        hotel_cal_obj = self.env['bus.hotel.calendar']
        for record in self:
            hotel_cal_obj.send_reservation_notification(
                naction,
                ntype,
                ntitle,
                record.product_id.id,
                record.id,
                record.partner_id.name,
                record.adults,
                record.children,
                record.checkin,
                record.checkout,
                record.folio_id.id,
                record.reserve_color,
                record.splitted,
                record.parent_reservation and
                record.parent_reservation.id or 0,
                record.product_id.name,
                record.partner_id.mobile
                or record.partner_id.phone or _('Undefined'),
                record.state,
                record.splitted)

    @api.model
    def create(self, vals):
        reservation_id = super(HotelReservation, self).create(vals)
        reservation_id.send_bus_notification('create',
                                             'notify',
                                             _("Reservation Created"))
        return reservation_id

    @api.multi
    def write(self, vals):
        ret = super(HotelReservation, self).write(vals)
        if vals.get('partner_id') or vals.get('checkin') or \
                vals.get('checkout') or vals.get('product_id') or \
                vals.get('adults') or vals.get('children') or \
                vals.get('state') or vals.get('splitted') or \
                vals.get('reserve_color') or vals.get('product_id'):
            for record in self:
                record.send_bus_notification(
                    'write',
                    ('cancelled' == record.state) and 'warn' or 'notify',
                    ('cancelled' == record.state) and
                    _("Reservation Cancelled") or _("Reservation Changed")
                )
        elif not any(vals):
            self.send_bus_notification('write', 'noshow')
        return ret

    @api.multi
    def unlink(self):
        self.send_bus_notification('unlink',
                                   'warn',
                                   _("Reservation Deleted"))
        return super(HotelReservation, self).unlink()

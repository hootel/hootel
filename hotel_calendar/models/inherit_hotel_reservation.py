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
from openerp import models, api, _
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
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
                    '|',('parent_reservation', '=', master_reserv.id), ('id', '=', master_reserv.id),
                    ('splitted', '=', True),
                ])
            json_reservation_tooltips.update({
                reserv.id: (
                    reserv.folio_id.partner_id.name,
                    reserv.folio_id.partner_id.mobile or reserv.folio_id.partner_id.phone or _('Undefined'),
                    reserv.checkin,
                    num_split)
            })
        return (json_reservations, json_reservation_tooltips)

    @api.model
    def _hcalendar_room_data(self, rooms):
        pricelist_id = self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        json_rooms = []
        for room in rooms:
            room_type = self.env['hotel.room.type'].search([('cat_id', '=', room.categ_id.id)], limit=1)
            vrooms = self.env['hotel.virtual.room'].search(['|', ('room_ids', 'in', room.id), ('room_type_ids.id', '=', room.categ_id.id)])
            json_rooms.append((
                room.product_id.id,
                room.name,
                room.capacity,
                room.categ_id.id,
                room_type.code_type,
                room.shared_room,
                room.uom_id.id,
                room.sale_price_type == 'vroom' and ['pricelist', room.price_virtual_room.id, pricelist_id] or ['fixed', room.list_price],
                room.sale_price_type == 'vroom' and room.price_virtual_room.name or 'Fixed Price',
                vrooms.mapped('name')))
        return json_rooms

    @api.multi
    def get_hcalendar_reservations_data(self, dfrom, dto, domain, rooms):
        domain = domain or []
        date_start = datetime.strptime(dfrom, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)
        date_end = datetime.strptime(dto, DEFAULT_SERVER_DATETIME_FORMAT)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_end_str = date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        room_ids = rooms.mapped('product_id.id')
        domain.insert(0, ('product_id', 'in', room_ids))
        domain.insert(0, ('state', 'in', ['draft',
                                          'confirm',
                                          'booking',
                                          'done',
                                          False]))
        reservations_raw = self.env['hotel.reservation'].search(domain, order="checkin DESC, checkout ASC, adults DESC, children DESC")
        reservations_ld = self.env['hotel.reservation'].search([
            ('checkin', '>=', date_start_str),
            ('checkout', '<=', date_end_str)])
        reservations_lr = self.env['hotel.reservation'].search([
            ('checkout', '>=', date_start_str),
            ('checkin', '<=', date_end_str)])
        reservations = (reservations_ld | reservations_lr) & reservations_raw
        return self._hcalendar_reservation_data(reservations)

    @api.multi
    def get_hcalendar_pricelist_data(self, dfrom, dto):
        pricelist_id = self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        date_start = datetime.strptime(dfrom, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)
        date_end = datetime.strptime(dto, DEFAULT_SERVER_DATETIME_FORMAT)
        # Get Prices
        date_diff = abs((date_start - date_end).days) + 1
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
                    ndate.strftime("%d/%m/%Y"): prod_price_id and prod_price_id.price or vroom.product_id.lst_price
                })
            json_rooms_prices[pricelist_id].append({
                'room': vroom.id,
                'days': days,
                'title': vroom.name,
            })
        return json_rooms_prices

    @api.multi
    def get_hcalendar_restrictions_data(self, dfrom, dto):
        restriction_id = self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_restrictions_id')
        if restriction_id:
            restriction_id = int(restriction_id)
        date_start = datetime.strptime(dfrom, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)
        date_end = datetime.strptime(dto, DEFAULT_SERVER_DATETIME_FORMAT)
        # Get Prices
        date_diff = abs((date_start - date_end).days) + 1
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
        type_move = self.env['ir.values'].get_default('hotel.config.settings', 'type_move')
        user_id = self.env['res.users'].browse(self.env.uid)
        return {
            'divide_rooms_by_capacity': self.env['ir.values'].get_default('hotel.config.settings', 'divide_rooms_by_capacity'),
            'eday_week': self.env['ir.values'].get_default('hotel.config.settings', 'end_day_week'),
            'days': self.env['ir.values'].get_default('hotel.config.settings', 'default_num_days') or 'month',
            'allow_invalid_actions': type_move == 'allow_invalid',
            'assisted_movement': type_move == 'assisted',
            'default_arrival_hour': self.env['ir.values'].get_default('hotel.config.settings', 'default_arrival_hour'),
            'default_departure_hour': self.env['ir.values'].get_default('hotel.config.settings', 'default_departure_hour'),
            'show_notifications': user_id.pms_show_notifications,
        }

    @api.multi
    def get_hcalendar_all_data(self, dfrom, dto, domainRooms, domainReservations, withRooms=True, withPricelist=True, withRestrictions=True):
        if not dfrom or not dto:
            raise ValidationError('Input Error: No dates defined!')

        domainRooms = domainRooms or []
        domainReservations = domainReservations or []

        rooms = self.env['hotel.room'].search(domainRooms)
        json_reservations, json_reservation_tooltips = self.get_hcalendar_reservations_data(dfrom, dto, domainReservations, rooms)
        vals = {
            'rooms': withRooms and self._hcalendar_room_data(rooms) or [],
            'reservations': json_reservations,
            'tooltips': json_reservation_tooltips,
            'pricelist': withPricelist and self.get_hcalendar_pricelist_data(dfrom, dto) or {},
            'restrictions': withRestrictions and self.get_hcalendar_restrictions_data(dfrom, dto) or {},
        }

        return vals

#     @api.multi
#     def get_vroom_price(self, product_id, checkin, checkout):
#         product = self.env['product.product'].browse([product_id])
#         partner = self.env['res.users'].browse(self.env.uid).partner_id
#
#         date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT)
#         date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT)
#         date_diff = abs((date_start - date_end).days)
#
#         total_price = 0.0
#         priceday = []
#         for i in range(0, date_diff - 1):
#             ndate = date_start + timedelta(days=i)
#             ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
#             prod = product.with_context(
#                 lang=partner.lang,
#                 partner=partner.id,
#                 quantity=1,
#                 date_order=ndate_str,
#                 pricelist=partner.property_product_pricelist.id,
#                 uom=product.product_tmpl_id.uom_id.id)
#             priceday.append({
#                 'date': ndate_str,
#                 'price': prod.price,
#             })
#             total_price += prod.price
#         return {'total_price': total_price, 'priceday': priceday}

    @api.model
    def create(self, vals):
        reservation_id = super(HotelReservation, self).create(vals)
        self.env['bus.hotel.calendar'].send_reservation_notification(
            'create',
            'notify',
            _("Reservation Created"),
            reservation_id.product_id.id,
            reservation_id.id,
            reservation_id.partner_id.name,
            reservation_id.adults,
            reservation_id.children,
            reservation_id.checkin,
            reservation_id.checkout,
            reservation_id.folio_id.id,
            reservation_id.reserve_color,
            reservation_id.splitted,
            reservation_id.parent_reservation.id,
            reservation_id.product_id.name,
            reservation_id.partner_id.mobile or reservation_id.partner_id.phone or _('Undefined'),
            reservation_id.state,
            reservation_id.splitted)
        return reservation_id

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelReservation, self).write(vals)
        for record in self:
            partner_id = vals.get('partner_id') and self.env['res.partner'].browse(vals.get('partner_id')) or record.partner_id
            checkin = vals.get('checkin') or record.checkin
            checkout = vals.get('checkout') or record.checkout
            product_id = vals.get('product_id') and self.env['product.product'].browse(vals.get('product_id')) or record.product_id
            adults = vals.get('adults') or record.adults
            children = vals.get('children') or record.children
            folio_id = vals.get('folio_id') and self.env['hotel.folio'].browse(vals.get('folio_id')) or record.folio_id
            color = vals.get('reserve_color') or record.reserve_color
            state = vals.get('state') or record.state
            splitted = vals.get('splitted') or record.splitted
            parent_reservation = vals.get('parent_reservation') and self.env['hotel.reservation'].browse(vals.get('parent_reservation')) or record.parent_reservation

            self.env['bus.hotel.calendar'].send_reservation_notification(
                'write',
                ('cancelled' == vals.get('state')) and 'warn' or 'notify',
                ('cancelled' == vals.get('state')) and _("Reservation Cancelled") or _("Reservation Changed"),
                product_id.id,
                record.id,
                partner_id.name,
                adults,
                children,
                checkin,
                checkout,
                folio_id.id,
                color,
                splitted,
                parent_reservation.id,
                product_id.name,
                partner_id.mobile or partner_id.phone or _('Undefined'),
                state,
                splitted)
        return ret_vals

    @api.multi
    def unlink(self):
        for record in self:
            self.env['bus.hotel.calendar'].send_reservation_notification(
                'unlink',
                'warn',
                _("Reservation Deleted"),
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
                reserv.parent_reservation.id,
                record.product_id.name,
                record.partner_id.mobile or record.partner_id.phone or _('Undefined'),
                record.state,
                record.splitted)
        return super(HotelReservation, self).unlink()

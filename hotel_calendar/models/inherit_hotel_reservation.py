# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
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
from openerp.exceptions import except_orm, UserError, ValidationError
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def get_hcalendar_data(self, checkin, checkout, domainRooms, domainReservations, withRooms=True):
        if not checkin or not checkout:
            return {
                'rooms': [],
                'reservations': [],
                'tooltips': {},
                'pricelist': {}
            }
            
        pricelist_id = int(self.env['ir.property'].search([('name', '=', 'property_product_pricelist')], limit=1).value_reference.split(',')[1])

        domainRooms = domainRooms or []
        domainReservations = domainReservations or []

        # Need move one day less
        date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)
        date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)

        # Get Rooms
        rooms = self.env['hotel.room'].search(domainRooms)
        json_rooms = []
        for room in rooms:
            room_type = self.env['hotel.room.type'].search([('cat_id', '=', room.categ_id.id)], limit=1)
            json_rooms.append((
                room.product_id.id,
                room.name,
                room.capacity,
                room.categ_id.id,
                room_type.code_type,
                room.shared_room,
                room.uom_id.id,
                room.sale_price_type == 'vroom' and ['pricelist', room.price_virtual_room.id, pricelist_id] or ['fixed', room.list_price]))

        # Get Reservations
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_end_str = date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        room_ids = rooms.mapped('product_id.id')
        domainReservations.insert(0, ('product_id', 'in', room_ids))
        domainReservations.insert(0, ('state', 'in', ['draft',
                                                      'confirm',
                                                      'booking',
                                                      'done',
                                                      False]))
        reservations_raw = self.env['hotel.reservation'].search(domainReservations, order="checkin DESC, checkout ASC, adults DESC, children DESC")
        reservations_ld = self.env['hotel.reservation'].search([
            ('checkin', '>=', date_start_str),
            ('checkout', '<=', date_end_str)])
        reservations_lr = self.env['hotel.reservation'].search([
            ('checkout', '>=', date_start_str),
            ('checkin', '<=', date_end_str)])
        reservations = (reservations_ld | reservations_lr) & reservations_raw
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
                False,  # Read-Only
                False,   # Fix Days
                False))  # Fix Rooms
            json_reservation_tooltips.update({
                reserv.id: (
                    reserv.folio_id.partner_id.name,
                    reserv.folio_id.partner_id.mobile or reserv.folio_id.partner_id.phone or _('Undefined'),
                    reserv.checkin)
            })

        # Get Prices
        price_list_global = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('compute_price', '=', 'fixed'),
            ('applied_on', '=', '3_global')
        ], order='sequence ASC, id DESC', limit=1)

        date_diff = abs((date_start - date_end).days)
        json_rooms_prices = {pricelist_id: []}
        vrooms = self.env['hotel.virtual.room'].search([])
        for vroom in vrooms:
            days = {}
            for i in range(0, date_diff + 1):
                ndate = date_start + timedelta(days=i)
                price_list = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist_id),
                    ('applied_on', '=', '1_product'),
                    ('product_tmpl_id', '=', vroom.product_id.product_tmpl_id.id),
                    ('date_start', '>=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('date_end', '<=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('compute_price', '=', 'fixed'),
                ], order='sequence ASC, id DESC', limit=1)
                _logger.info(price_list.fixed_price)
                days.update({
                    ndate.strftime("%d/%m/%Y"): (price_list and price_list.fixed_price) or (price_list_global and price_list_global.fixed_price) or 0.0
                })
            json_rooms_prices[pricelist_id].append({
                'room': vroom.id,
                'days': days,
                'title': vroom.name,
            })

        return {
            'rooms': withRooms and json_rooms or [],
            'reservations': json_reservations,
            'tooltips': json_reservation_tooltips,
            'pricelist': json_rooms_prices,
        }

    @api.multi
    def get_vroom_price(self, product_id, checkin, checkout):
        product = self.env['product.product'].browse([product_id])
        partner = self.env['res.users'].browse(self.env.uid).partner_id

        date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT)
        date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT)
        date_diff = abs((date_start - date_end).days)

        total_price = 0.0
        priceday = []
        for i in range(0, date_diff - 1):
            ndate = date_start + timedelta(days=i)
            ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
            prod = product.with_context(
                lang=partner.lang,
                partner=partner.id,
                quantity=1,
                date_order=ndate_str,
                pricelist=partner.property_product_pricelist.id,
                uom=product.product_tmpl_id.uom_id.id)
            priceday.append({
                'date': ndate_str,
                'price': prod.price,
            })
            total_price += prod.price
        return {'total_price': total_price, 'priceday': priceday}

    @api.model
    def create(self, vals):
        reservation_id = super(HotelReservation, self).create(vals)
        self.env['bus.hotel.calendar'].send_notification(
            'notify',
            _("Reservation Created"),
            reservation_id.partner_id.name,
            reservation_id.checkin,
            reservation_id.checkout,
            reservation_id.product_id.name,
        )
        return reservation_id

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelReservation, self).write(vals)
        partner_id = self.partner_id
        checkin = self.checkin
        checkout = self.checkout
        product_id = self.product_id
        state = self.state
        new_state = False
        need_send_notif = False
        if vals.get('partner_id'):
            partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
            need_send_notif = True
        if vals.get('checkin'):
            checkin = vals.get('checkin')
            need_send_notif = True
        if vals.get('checkout'):
            checkout = vals.get('checkout')
            need_send_notif = True
        if vals.get('product_id'):
            product_id = self.env['product.product'].browse(vals.get('product_id'))
            need_send_notif = True
        if vals.get('state'):
            state = vals.get('state')
            need_send_notif = True
            new_state = True

        if need_send_notif:
            self.env['bus.hotel.calendar'].send_notification(
                (new_state and state == 'cancelled') and 'warn' or 'notify',
                (new_state and state == 'cancelled') and _("Reservation Cancelled") or _("Reservation Changed"),
                partner_id.name,
                checkin,
                checkout,
                product_id.name
            )
        return ret_vals

    @api.multi
    def unlink(self):
        self.env['bus.hotel.calendar'].send_notification(
            'warn',
            _("Reservation Deleted"),
            self.partner_id.name,
            self.checkin,
            self.checkout,
            self.product_id.name
        )
        return super(HotelReservation, self).unlink()

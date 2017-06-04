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
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

PUBLIC_PRICELIST_ID = 1  # Hard-Coded public pricelist


class HotelFolio(models.Model):
    _inherit = "hotel.folio"

    @api.multi
    def get_hcalendar_data(self, checkin, checkout, domainRooms, domainReservations, withRooms=True):
        if not checkin or not checkout:
            return {
                'rooms': [],
                'reservations': [],
                'tooltips': {},
                'pricelist': {}
            }

        domainRooms = domainRooms or []
        domainReservations = domainReservations or []

        # Need move one day less
        date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)
        date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)

        _logger.info(date_start)
        _logger.info(date_end)
 
        # Get Rooms
        rooms = self.env['hotel.room'].search(domainRooms)
        json_rooms = []
        for room in rooms:
            json_rooms.append((
                room.product_id.id,
                room.name,
                room.capacity,
                room.categ_id.id,
                room.categ_id.name,
                room.shared_room,
                room.uom_id.id))

        # Get Reservations
        room_ids = rooms.mapped('product_id.id')
        domainReservations.insert(0, ('product_id.id', 'in', room_ids))
        domainReservations.insert(0, ('checkin', '<=', date_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
        domainReservations.insert(0, ('checkout', '>=', date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
        reservations = self.env['hotel.reservation'].search(domainReservations, order="checkin DESC, checkout ASC, adults DESC, children DESC")
        json_reservations = []
        json_reservation_tooltips = {}
        for reserv in reservations:
            #r_cin = datetime.strptime(reserv.checkin, DEFAULT_SERVER_DATETIME_FORMAT)
            #r_cout = datetime.strptime(reserv.checkout, DEFAULT_SERVER_DATETIME_FORMAT)
            #if r_cin >= date_end or r_cout < date_start:
            #    continue
            json_reservations.append((
                reserv.product_id.id,
                reserv.id,
                reserv.folio_id.partner_id.name,
                reserv.adults,
                reserv.children,
                reserv.checkin,
                reserv.checkout,
                reserv.folio_id.id,
                reserv.reserve_color))
            json_reservation_tooltips.update({
                reserv.id: (
                    reserv.folio_id.partner_id.name,
                    reserv.folio_id.partner_id.mobile or reserv.folio_id.partner_id.phone or _('Undefined'),
                    reserv.checkin)
                })

        # Get Prices
        price_list_global = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', PUBLIC_PRICELIST_ID),
            ('compute_price', '=', 'fixed'),
            ('applied_on', '=', '3_global')
        ], order='sequence ASC, id DESC', limit=1)
        categs = rooms.mapped('categ_id')
        date_diff = abs((date_start-date_end).days)+1
        json_rooms_prices = {}
        for cat in categs:
            json_rooms_prices.update({cat.name: {}})
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                price_list = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', PUBLIC_PRICELIST_ID), # FIXME: Hard-Coded Public List ID
                    ('applied_on', '=', '2_product_category'),
                    ('categ_id', '=', cat.id),
                    ('date_start', '<=', ndate.replace(hour=0, minute=0, second=0).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                    ('date_end', '>=', ndate.replace(hour=23, minute=59, second=59).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                    ('compute_price', '=', 'fixed'),
                ], order='sequence ASC, id DESC', limit=1)
                json_rooms_prices[cat.name].update({
                    ndate.strftime(DEFAULT_SERVER_DATE_FORMAT): (price_list and price_list.fixed_price) or (price_list_global and price_list_global.fixed_price) or 0.0
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
        date_diff = abs((date_start-date_end).days)+1

        price = 0.0
        for i in range(0, date_diff-1):
            ndate = date_start + timedelta(days=i)
            prod = product.with_context(
                lang=partner.lang,
                partner=partner.id,
                quantity=1,
                date_order=ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                pricelist=partner.property_product_pricelist.id,
                uom=product.product_tmpl_id.uom_id.id)
            price += prod.price
        return {'unit_price': price}

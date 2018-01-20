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
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from openerp import models, api
from openerp.exceptions import ValidationError
from odoo.addons.hotel import date_utils
import logging
_logger = logging.getLogger(__name__)


class HotelCalendarManagement(models.TransientModel):
    _name = 'hotel.calendar.management'

    @api.multi
    def save_changes(self, pricelist_id, restriction_id, pricelist,
                     restrictions, availability):
        vroom_obj = self.env['hotel.virtual.room']
        product_pricelist_item_obj = self.env['product.pricelist.item']
        vroom_rest_item_obj = self.env['hotel.virtual.room.restriction.item']
        vroom_avail_obj = self.env['hotel.virtual.room.availability']

        # Save Pricelist
        for k_price, v_price in pricelist.iteritems():
            vroom_id = vroom_obj.browse([int(k_price)])
            vroom_prod_tmpl_id = vroom_id.product_id.product_tmpl_id
            for price in v_price:
                price_id = product_pricelist_item_obj.search([
                    ('date_start', '>=', price['date']),
                    ('date_end', '<=', price['date']),
                    ('pricelist_id', '=', int(pricelist_id)),
                    ('applied_on', '=', '1_product'),
                    ('compute_price', '=', 'fixed'),
                    ('product_tmpl_id', '=', vroom_prod_tmpl_id.id),
                ], limit=1)
                if not price_id:
                    product_pricelist_item_obj.create({
                        'date_start': price['date'],
                        'date_end': price['date'],
                        'pricelist_id': int(pricelist_id),
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'fixed_price': price['price'],
                        'product_tmpl_id': vroom_prod_tmpl_id.id,
                    })
                else:
                    price_id.write({
                        'fixed_price': price['price']
                    })

        # Save Restrictions
        for k_res, v_res in restrictions.iteritems():
            for restriction in v_res:
                res_id = vroom_rest_item_obj.search([
                    ('date_start', '>=', restriction['date']),
                    ('date_end', '<=', restriction['date']),
                    ('restriction_id', '=', int(restriction_id)),
                    ('applied_on', '=', '0_virtual_room'),
                    ('virtual_room_id', '=', int(k_res)),
                ], limit=1)
                if not res_id:
                    vroom_rest_item_obj.create({
                        'date_start': restriction['date'],
                        'date_end': restriction['date'],
                        'restriction_id': int(restriction_id),
                        'applied_on': '0_virtual_room',
                        'virtual_room_id': int(k_res),
                        'min_stay': restriction['min_stay'],
                        'min_stay_arrival': restriction['min_stay_arrival'],
                        'max_stay': restriction['max_stay'],
                        'closed': restriction['closed'],
                        'closed_arrival': restriction['closed_arrival'],
                        'closed_departure': restriction['closed_departure'],
                    })
                else:
                    res_id.write({
                        'min_stay': restriction['min_stay'],
                        'min_stay_arrival': restriction['min_stay_arrival'],
                        'max_stay': restriction['max_stay'],
                        'closed': restriction['closed'],
                        'closed_arrival': restriction['closed_arrival'],
                        'closed_departure': restriction['closed_departure'],
                    })

        # Save Availability
        for k_avail, v_avail in availability.iteritems():
            vroom_id = vroom_obj.browse(int(k_avail))
            for avail in v_avail:
                cavail = len(vroom_obj.check_availability_virtual_room(
                    avail['date'], avail['date'], virtual_room_id=vroom_id.id))
                ravail = min(cavail, vroom_id.total_rooms_count,
                             int(avail['avail']))
                avail_id = vroom_avail_obj.search([
                    ('date', '=', avail['date']),
                    ('virtual_room_id', '=', vroom_id.id),
                ], limit=1)
                if not avail_id:
                    vroom_avail_obj.create({
                        'date': avail['date'],
                        'no_ota': avail['no_ota'],
                        'avail': ravail,
                        'virtual_room_id': vroom_id.id,
                    })
                else:
                    avail_id.write({
                        'no_ota': avail['no_ota'],
                        'avail': ravail,
                    })
        return True

    def _hcalendar_room_json_data(self, rooms):
        json_data = []
        for room in rooms:
            json_data.append((
                room.id,
                room.name,
                room.get_capacity(),
                room.list_price,
                room.max_real_rooms,
            ))
        return json_data

    def _hcalendar_pricelist_json_data(self, prices):
        json_data = {}
        vroom_obj = self.env['hotel.virtual.room']
        for rec in prices:
            virtual_room_id = vroom_obj.search([
                ('product_id.product_tmpl_id', '=', rec.product_tmpl_id.id)
            ], limit=1)
            if not virtual_room_id:
                continue

            # TODO: date_end - date_start loop
            json_data.setdefault(virtual_room_id.id, []).append({
                'id': rec.id,
                'price': rec.fixed_price,
                'date': rec.date_start,
            })
        return json_data

    def _hcalendar_restriction_json_data(self, restrictions):
        json_data = {}
        for rec in restrictions:
            # TODO: date_end - date_start loop
            json_data.setdefault(rec.virtual_room_id.id, []).append({
                'id': rec.id,
                'date': rec.date_start,
                'min_stay': rec.min_stay,
                'min_stay_arrival': rec.min_stay_arrival,
                'max_stay': rec.max_stay,
                'closed': rec.closed,
                'closed_departure': rec.closed_departure,
                'closed_arrival': rec.closed_arrival,
            })
        return json_data

    @api.model
    def _hcalendar_availability_json_data(self, dfrom, dto):
        date_start = date_utils.get_datetime(dfrom, hours=False)
        date_diff = date_utils.date_diff(dfrom, dto, hours=False) + 1
        vrooms = self.env['hotel.virtual.room'].search([])
        json_data = {}

        for vroom in vrooms:
            json_data[vroom.id] = []
            for i in range(0, date_diff):
                cur_date = date_start + timedelta(days=i)
                cur_date_str = cur_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                avail = self.env['hotel.virtual.room.availability'].search([
                    ('date', '=', cur_date_str),
                    ('virtual_room_id', '=', vroom.id)
                ])
                if avail:
                    json_data[vroom.id].append({
                        'id': vroom.id,
                        'date': avail.date,
                        'avail': avail.avail,
                        'no_ota': avail.no_ota,
                    })
                else:
                    json_data[vroom.id].append({
                        'id': False,
                        'date': cur_date_str,
                        'avail': vroom.max_real_rooms,
                        'no_ota': False,
                    })
        return json_data

    def _hcalendar_get_count_reservations_json_data(self, dfrom, dto):
        vrooms = self.env['hotel.virtual.room'].search([])
        date_start = date_utils.get_datetime(dfrom, hours=False)
        date_diff = date_utils.date_diff(dfrom, dto, hours=False) + 1
        hotel_vroom_obj = self.env['hotel.virtual.room']
        hotel_room_obj = self.env['hotel.room']
        hotel_reservation_obj = self.env['hotel.reservation']
        vrooms = hotel_vroom_obj.search([])

        nn = {}
        for i in range(0, date_diff):
            cur_date = date_start + timedelta(days=i)
            cur_date_str = cur_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            occupied_reservations = hotel_reservation_obj.occupied(
                '%s 00:00:00' % cur_date_str,
                '%s 00:00:00' % cur_date_str)

            if cur_date not in nn:
                nn.update({cur_date_str: {}})
            if not any(occupied_reservations):
                for vroom in vrooms:    # Recorremos habs virtuales ocupadas
                    if vroom.id not in nn[cur_date_str]:
                        nn[cur_date_str][vroom.id] = 0
            else:
                for oreserv in occupied_reservations:
                    occupied_room = hotel_room_obj.search([
                        ('product_id', '=', oreserv.product_id.id)
                    ], limit=1)
                    occupied_vrooms = hotel_vroom_obj.search([
                        '|', ('room_ids', 'in', [occupied_room.id]),
                             ('room_type_ids', 'in', [
                                                    occupied_room.categ_id.id])
                    ])

                    if cur_date_str not in nn:
                        nn.update({cur_date_str: {}})
                    for vroom in vrooms:    # Recorremos habs. virt. ocupadas
                        if vroom.id not in nn[cur_date_str]:
                            nn[cur_date_str][vroom.id] = 0
                        if vroom.id in occupied_vrooms.ids:
                            nn[cur_date_str][vroom.id] += 1

        json_data = {}
        for date in nn:
            for vroom in nn[date]:
                if vroom not in json_data:
                    json_data[vroom] = []
                json_data[vroom].append({
                    'date': date,
                    'num': nn[date][vroom],
                })

        return json_data

    @api.multi
    def get_hcalendar_all_data(self, dfrom, dto, pricelist_id, restriction_id,
                               withRooms):
        if not dfrom or not dto:
            raise ValidationError('Input Error: No dates defined!')
        vals = {}
        if not pricelist_id:
            pricelist_id = self.env['ir.values'].sudo().get_default(
                            'hotel.config.settings', 'parity_pricelist_id')
        if not restriction_id:
            restriction_id = self.env['ir.values'].sudo().get_default(
                            'hotel.config.settings', 'parity_restrictions_id')

        pricelist_id = int(pricelist_id)
        vals.update({'pricelist_id': pricelist_id})
        restriction_id = int(restriction_id)
        vals.update({'restriction_id': restriction_id})

        vroom_rest_it_obj = self.env['hotel.virtual.room.restriction.item']
        restriction_item_ids = vroom_rest_it_obj.search([
            ('date_start', '>=', dfrom), ('date_end', '<=', dto),
            ('restriction_id', '=', restriction_id),
            ('applied_on', '=', '0_virtual_room'),
        ])

        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('date_start', '>=', dfrom), ('date_end', '<=', dto),
            ('pricelist_id', '=', pricelist_id),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
        ])

        json_prices = self._hcalendar_pricelist_json_data(pricelist_item_ids)
        json_rest = self._hcalendar_restriction_json_data(restriction_item_ids)
        json_avails = self._hcalendar_availability_json_data(dfrom, dto)
        json_rc = self._hcalendar_get_count_reservations_json_data(dfrom, dto)
        vals.update({
            'prices': json_prices or [],
            'restrictions': json_rest or [],
            'availability': json_avails or [],
            'count_reservations': json_rc or [],
        })

        if withRooms:
            room_ids = self.env['hotel.virtual.room'].search([])
            json_rooms = self._hcalendar_room_json_data(room_ids)
            vals.update({'rooms': json_rooms or []})

        return vals

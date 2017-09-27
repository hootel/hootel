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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, api
import logging
_logger = logging.getLogger(__name__)

class HotelCalendarManagement(models.TransientModel):
    _name = 'hotel.calendar.management'

    @api.multi
    def save_changes(self, pricelist_id, restriction_id, pricelist, restrictions, availability):
        # Save Pricelist
        for k_price in pricelist.keys():
            room_id = self.env['hotel.virtual.room'].browse([int(k_price)])
            for price in pricelist[k_price]:
                price_id = self.env['product.pricelist.item'].search([
                    ('date_start', '>=', price['date']), ('date_end', '<=', price['date']),
                    ('pricelist_id', '=', int(pricelist_id)),
                    ('applied_on', '=', '1_product'),
                    ('compute_price', '=', 'fixed'),
                    ('product_tmpl_id', '=', room_id.product_id.product_tmpl_id.id),
                ], limit=1)
                if not price_id:
                    self.env['product.pricelist.item'].create({
                        'date_start': price['date'],
                        'date_end': price['date'],
                        'pricelist_id': int(pricelist_id),
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'fixed_price': price['price'],
                        'product_tmpl_id': room_id.product_id.product_tmpl_id.id,
                    })
                else:
                    price_id.write({
                        'fixed_price': price['price']
                    })

        # Save Restrictions
        for k_res in restrictions.keys():
            for restriction in restrictions[k_res]:
                res_id = self.env['hotel.virtual.room.restriction.item'].search([
                    ('date_start', '>=', restriction['date']), ('date_end', '<=', restriction['date']),
                    ('restriction_id', '=', int(restriction_id)),
                    ('applied_on', '=', '0_virtual_room'),
                    ('virtual_room_id', '=', int(k_res)),
                ], limit=1)
                if not res_id:
                    self.env['hotel.virtual.room.restriction.item'].create({
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
        for k_avail in availability.keys():
            for avail in availability[k_avail]:
                avail_id = self.env['hotel.virtual.room.availabity'].search([
                    ('date', '=', avail['date']),
                    ('virtual_room_id', '=', int(k_avail)),
                ], limit=1)
                if not avail_id:
                    self.env['hotel.virtual.room.availabity'].create({
                        'date': avail['date'],
                        'no_ota': avail['no_ota'],
                        'avail': avail['avail'],
                        'virtual_room_id': int(k_avail),
                    })
                else:
                    avail_id.write({
                        'no_ota': avail['no_ota'],
                        'avail': avail['avail'],
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
            ))
        return json_data

    def _hcalendar_pricelist_json_data(self, prices):
        json_data = {}
        for rec in prices:
            virtual_room_id = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', rec.product_tmpl_id.id)], limit=1)
            if not virtual_room_id:
                continue

            if virtual_room_id.id not in json_data.keys():
                json_data.update({virtual_room_id.id: []})
            # TODO: date_end - date_start loop
            json_data[virtual_room_id.id].append({
                'id': rec.id,
                'price': rec.fixed_price,
                'date': rec.date_start,
            })
        return json_data

    def _hcalendar_restriction_json_data(self, restrictions):
        json_data = {}
        for rec in restrictions:
            if rec.virtual_room_id.id not in json_data.keys():
                json_data.update({rec.virtual_room_id.id: []})
            # TODO: date_end - date_start loop
            json_data[rec.virtual_room_id.id].append({
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

    def _hcalendar_availability_json_data(self, avails):
        json_data = {}
        for rec in avails:
            if rec.virtual_room_id.id not in json_data.keys():
                json_data.update({rec.virtual_room_id.id: []})
            json_data[rec.virtual_room_id.id].append({
                'id': rec.id,
                'date': rec.date,
                'avail': rec.avail,
                'no_ota': rec.no_ota,
            })
        return json_data

    @api.multi
    def get_hcalendar_all_data(self, dfrom, dto, pricelist_id, restriction_id, withRooms):
        if not dfrom or not dto:
            raise ValidationError('Input Error: No dates defined!')
        vals = {}
        if not pricelist_id:
            pricelist_id = int(self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_pricelist_id'))
            vals.update({'pricelist_id': pricelist_id})
        if not restriction_id:
            restriction_id = int(self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_restrictions_id'))
            vals.update({'restriction_id': restriction_id})

        avail_ids = self.env['hotel.virtual.room.availabity'].search([
            ('date', '>=', dfrom), ('date', '<=', dto),
        ])
        restriction_item_ids = self.env['hotel.virtual.room.restriction.item'].search([
            ('date_start', '>=', dfrom), ('date_end', '<=', dto),
            ('restriction_id', '=', int(restriction_id)),
            ('applied_on', '=', '0_virtual_room'),
        ])

        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('date_start', '>=', dfrom), ('date_end', '<=', dto),
            ('pricelist_id', '=', int(pricelist_id)),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
        ])

        vals.update({
            'prices': self._hcalendar_pricelist_json_data(pricelist_item_ids) or [],
            'restrictions': self._hcalendar_restriction_json_data(restriction_item_ids) or [],
            'availability': self._hcalendar_availability_json_data(avail_ids) or [],
        })

        if withRooms:
            room_ids = self.env['hotel.virtual.room'].search([])
            vals.update({'rooms': self._hcalendar_room_json_data(room_ids) or []})

        return vals

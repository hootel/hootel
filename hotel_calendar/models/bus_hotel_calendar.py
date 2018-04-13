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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, api
from odoo.addons.hotel_calendar.controllers.bus import HOTEL_BUS_CHANNEL_ID


class BusHotelCalendar(models.TransientModel):
    _name = 'bus.hotel.calendar'

    '''
    action:
        - create
        - write
        - unlink
        - cancelled
    ntype:
        - notif : Show a normal notification
        - warn : Show a warning notification
        - noshow : Don't show any notification
    '''
    @api.model
    def _generate_reservation_notif(self, vals):
        user_id = self.env['res.users'].browse(self.env.uid)
        master_reserv = vals['parent_reservation'] or vals['reserv_id']
        num_split = self.env['hotel.reservation'].search_count([
            ('folio_id', '=', vals['folio_id']),
            '|', ('parent_reservation', '=', master_reserv),
                 ('id', '=', master_reserv),
            ('splitted', '=', True),
        ])
        return {
            'type': 'reservation',
            'action': vals['action'],
            'subtype': vals['type'],
            'title': vals['title'],
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'reservation': {
                'product_id': vals['product_id'],
                'reserv_id': vals['reserv_id'],
                'partner_name': vals['partner_name'],
                'adults': vals['adults'],
                'childer': vals['children'],
                'checkin': vals['checkin'],
                'checkout': vals['checkout'],
                'folio_id': vals['folio_id'],
                'reserve_color': vals['reserve_color'],
                'reserve_color_text': vals['reserve_color_text'],
                'splitted': vals['splitted'],
                'parent_reservation': vals['parent_reservation'],
                'room_name': vals['room_name'],
                'state': vals['state'],
                'only_read': False,
                'fix_days': vals['fix_days'],
                'fix_rooms': False,
                'overbooking': vals['overbooking'],
            },
            'tooltip': [
                vals['partner_name'],
                vals['partner_phone'],
                vals['checkin'],
                num_split,
            ]
        }

    @api.model
    def _generate_pricelist_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'pricelist',
            'price': {
                vals['pricelist_id']: [{
                    'days': {
                        date_dt.strftime("%d/%m/%Y"): vals['price'],
                    },
                    'room': vals['virtual_room_id'],
                    'id': vals['id'],
                }],
            },
        }

    @api.model
    def _generate_restriction_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'restriction',
            'restriction': {
                vals['virtual_room_id']: {
                    date_dt.strftime("%d/%m/%Y"): [
                        vals['min_stay'],
                        vals['min_stay_arrival'],
                        vals['max_stay'],
                        vals['max_stay_arrival'],
                        vals['closed'],
                        vals['closed_arrival'],
                        vals['closed_departure'],
                        vals['id'],
                    ],
                },
            },
        }

    @api.model
    def _generate_availability_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'availability',
            'availability': {
                vals['virtual_room_id']: {
                    date_dt.strftime("%d/%m/%Y"): [
                        vals['avail'],
                        vals['no_ota'],
                        vals['id'],
                    ],
                },
            },
        }

    @api.model
    def send_reservation_notification(self, vals):
        notif = self._generate_reservation_notif(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_pricelist_notification(self, vals):
        notif = self._generate_pricelist_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_restriction_notification(self, vals):
        notif = self._generate_restriction_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_availability_notification(self, vals):
        notif = self._generate_availability_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

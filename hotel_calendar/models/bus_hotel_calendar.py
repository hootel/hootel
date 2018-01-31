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

    # FIXME: Too many parameters... perhaps best use kargs?
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
    def _generate_reservation_notif(self, action, ntype, title,
                                    product_id, reserv_id, partner_name,
                                    adults, children, checkin, checkout,
                                    folio_id, color, splitted,
                                    parent_reservation, room_name,
                                    partner_phone, state, fix_days):
        user_id = self.env['res.users'].browse(self.env.uid)
        master_reserv = parent_reservation or reserv_id
        num_split = self.env['hotel.reservation'].search_count([
            ('folio_id', '=', folio_id),
            '|', ('parent_reservation', '=', master_reserv),
                 ('id', '=', master_reserv),
            ('splitted', '=', True),
        ])
        return {
            'type': 'reservation',
            'action': action,
            'subtype': ntype,
            'title': title,
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'reservation': {
                'product_id': product_id,
                'reserv_id': reserv_id,
                'partner_name': partner_name,
                'adults': adults,
                'childer': children,
                'checkin': checkin,
                'checkout': checkout,
                'folio_id': folio_id,
                'reserve_color': color,
                'splitted': splitted,
                'parent_reservation': parent_reservation,
                'room_name': room_name,
                'state': state,
                'only_read': False,
                'fix_days': fix_days,
                'fix_rooms': False,
            },
            'tooltip': [
                partner_name,
                partner_phone,
                checkin,
                num_split,
            ]
        }

    @api.model
    def _generate_pricelist_notification(self, pricelist, date, vroom, price):
        date_dt = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'pricelist',
            'price': {
                'pricelist': [{
                    'days': {
                        date_dt.strftime("%d/%m/%Y"): price,
                    },
                    'room': vroom,
                }],
            },
        }

    # FIXME: Too many parameters... perhaps best use kargs?
    @api.model
    def send_reservation_notification(self, action, ntype, title, product_id,
                                      reserv_id, partner_name, adults,
                                      children, checkin, checkout, folio_id,
                                      color, splitted, parent_reservation,
                                      room_name, partner_phone, state,
                                      fix_days):
        notif = self._generate_reservation_notif(action, ntype, title,
                                                 product_id, reserv_id,
                                                 partner_name, adults,
                                                 children, checkin,
                                                 checkout, folio_id,
                                                 color, splitted,
                                                 parent_reservation,
                                                 room_name, partner_phone,
                                                 state, fix_days)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_pricelist_notification(self, pricelist, date, vroom, price):
        notif = self._generate_pricelist_notification(pricelist, date, vroom,
                                                      price)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

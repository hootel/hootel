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
from openerp import models, api


class BusHotelCalendar(models.TransientModel):
    _name = 'bus.hotel.calendar'

    @api.model
    def _generate_reservation_notification(self, action, ntype, title, product_id,
                                           reserv_id, partner_name, adults,
                                           children, checkin, checkout,
                                           folio_id, color, room_name,
                                           partner_phone, state):
        user_id = self.env['res.users'].browse(self.env.uid)
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
                'room_name': room_name,
                'state': state,
                'only_read': False,
                'fix_days': False,
                'fix_rooms': False,
            },
            'tooltip': [
                partner_name,
                partner_phone,
                checkin
            ]
        }

    @api.model
    def send_reservation_notification(self, action, ntype, title, product_id,
                                      reserv_id, partner_name, adults, children,
                                      checkin, checkout, folio_id, color,
                                      room_name, partner_phone, state):
        notif = self._generate_reservation_notification(action, ntype, title,
                                                        product_id, reserv_id,
                                                        partner_name, adults,
                                                        children, checkin,
                                                        checkout, folio_id,
                                                        color, room_name,
                                                        partner_phone, state)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation', 'public'), notif)

    @api.model
    def send_pricelist_notification(self, ntype, title, name, checkin, checkout, room_name):
        user_id = self.env['res.users'].browse(self.env.uid)
        notification = {
            'type': 'reservation',
            'subtype': ntype,
            'title': title,
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'reservation': {
                'name': name,
                'checkin': checkin,
                'checkout': checkout,
                'room_name': room_name,
            },
        }
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation', 'public'), notification)

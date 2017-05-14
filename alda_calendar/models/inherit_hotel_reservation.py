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
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    @api.multi
    def get_hcalendar_data(self, domainRooms, domainReservations, withRooms=True):
        domainRooms = domainRooms or []
        domainReservations = domainReservations or []

        rooms = self.env['hotel.room'].search(domainRooms)
        json_rooms = []
        for room in rooms:
            json_rooms.append((
                room.id,
                room.name,
                room.capacity,
                room.categ_id.id,
                room.categ_id.name,
                room.shared_room))

        room_ids = rooms.mapped('id')
        domainReservations.append(('reservation_line.reserve.id', 'in', room_ids))
        reservations = self.env['hotel.reservation'].search(domainReservations, order="checkin DESC, checkout ASC, adults DESC, children DESC")
        json_reservations = []
        json_reservation_tooltips = {}
        for reserv in reservations:
            for line in reserv.reservation_line:
                for r in line.reserve:
                    if r.id in room_ids:
                        json_reservations.append((
                            r.id,
                            reserv.id,
                            reserv.partner_id.name,
                            line.adults,
                            line.children,
                            reserv.checkin,
                            reserv.checkout,
                            line.id))
                        json_reservation_tooltips.update({
                            reserv.id: (
                                reserv.partner_id.name,
                                reserv.partner_id.mobile or reserv.partner_id.phone or _('Undefined'),
                                reserv.checkin)
                            })

        return {
            'rooms': withRooms and json_rooms or [],
            'reservations': json_reservations,
            'tooltips': json_reservation_tooltips
        }

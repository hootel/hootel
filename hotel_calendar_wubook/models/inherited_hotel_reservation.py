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
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    @api.model
    def _generate_reservation_notif(self, action, ntype, title,
                                    product_id, reserv_id, partner_name,
                                    adults, children, checkin, checkout,
                                    folio_id, color, color_text, splitted,
                                    parent_reservation, room_name,
                                    partner_phone, state, fix_days):
        vals = super(HotelReservation, self)._generate_reservation_notif(
            action, ntype, title, product_id,
            reserv_id, partner_name, adults,
            children, checkin, checkout,
            folio_id, color, color_text, splitted, parent_reservation,
            room_name, partner_phone, state, fix_days)
        reserv = self.env['hotel.reservation'].browse(vals['reserv_id'])
        vals['reservation'].update({
            'fix_days': (reserv.wrid and reserv.wrid != '') or fix_days,
            'wchannel': (reserv.wchannel_id and reserv.wchannel_id.name),
        })
        return vals

    @api.multi
    def _hcalendar_reservation_data(self, reservations):
        vals = super(HotelReservation, self)._hcalendar_reservation_data(
                                                                reservations)
        hotel_reservation_obj = self.env['hotel.reservation']
        json_reservations = []
        for v_rval in vals[0]:
            reserv = hotel_reservation_obj.browse(v_rval[1])
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
                reserv.reserve_color_text,
                reserv.splitted,
                reserv.parent_reservation.id,
                # Read-Only
                False,
                # Fix Days
                (reserv.wrid and reserv.wrid != '') or reserv.splitted,
                # Fix Rooms
                False,
                reserv.overbooking))
            # Update tooltips
            vals[1][reserv.id].append(reserv.wchannel_id.name)
        return (json_reservations, vals[1])

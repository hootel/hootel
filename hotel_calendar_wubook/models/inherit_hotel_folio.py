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


class HotelFolio(models.Model):
    _inherit = "hotel.folio"

    @api.multi
    def get_hcalendar_data(self, checkin, checkout, domainRooms, domainReservations, withRooms=True):
        vals = super(HotelFolio, self).get_hcalendar_data(checkin, checkout,
                                                          domainRooms,
                                                          domainReservations,
                                                          withRooms=withRooms)
        hotel_reservation_obj = self.env['hotel.reservation']
        json_reservations = []
        for reserv_vals in vals['reservations']:
            reserv = hotel_reservation_obj.browse(reserv_vals[1])
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
                reserv.wis_from_channel))
        vals['reservations'] = json_reservations
        return vals

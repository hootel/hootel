# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
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
from odoo import fields
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
from odoo.addons.hotel import date_utils
import pytz


class TestCalendarOperations(TestHotelCalendar):

    def test_split_reservation(self):
        now_utc_dt = date_utils.now()
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio, reservation = self.create_reservation(
            self.user_hotel_manager,
            self.partner_2,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")

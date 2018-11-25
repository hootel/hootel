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
from datetime import timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.addons.hotel import date_utils
from .common import TestHotelWubook


class TestReservationRestrictionItem(TestHotelWubook):

    def test_write(self):
        now_utc_dt = date_utils.now()
        day_utc_dt = now_utc_dt + timedelta(days=20)
        day_utc_str = day_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        rest_item_obj = self.env['hotel.room.type.restriction.item']
        restriction = rest_item_obj.search([], limit=1)
        self.assertTrue(restriction, "Can't found restriction for test")
        restriction.write({
            'min_stay': 3,
            'date_start': day_utc_str
        })
        self.assertEqual(restriction.min_stay, 3, "Invalid Max Avail")
        self.assertEqual(restriction.date_start, day_utc_str, "Invalid Date")

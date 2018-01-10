# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
import logging
_logger = logging.getLogger(__name__)


class TestManagementCalendar(TestHotelCalendar):

    def test_calendar_pricelist(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restriction_id,
            True)

    def test_invalid_input_calendar_data(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.parity_pricelist_id,
                self.parity_restriction_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                False,
                self.parity_pricelist_id,
                self.parity_restriction_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                False,
                self.parity_pricelist_id,
                self.parity_restriction_id,
                True)
        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            False,
            False,
            True)
        self.assertTrue(any(hcal_data), "Hotel Calendar invalid default management parity models!")

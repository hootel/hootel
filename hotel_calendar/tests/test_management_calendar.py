# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel.tests.common import TestHotel
import logging
_logger = logging.getLogger(__name__)


class TestManagementCalendar(TestHotel):

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

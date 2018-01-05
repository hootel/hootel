# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel.tests.common import TestHotel
import logging
_logger = logging.getLogger(__name__)


class TestReservationsCalendar(TestHotel):

    def test_calendar_info_integrity(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hcal_data = self.env['hotel.reservation'].get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            [], [])

        # Check Pricelist Integrity
        for k_pr, v_pr in hcal_data['pricelist'].iteritems():
            for vroom_pr in v_pr:
                if vroom_pr['room'] in self.prices_tmp.keys(): # Only Check Test Cases
                    sorted_dates = sorted(vroom_pr['days'].keys(), key=lambda x: datetime.datetime.strptime(x, '%d/%m/%Y'))
                    init_date_dt = datetime.datetime.strptime(sorted_dates[0], '%d/%m/%Y')
                    end_date_dt = datetime.datetime.strptime(sorted_dates[-1], '%d/%m/%Y')

                    self.assertEqual(real_start_utc_dt, init_date_dt, "Hotel Calendar don't start in the correct date!")
                    self.assertEqual(adv_utc_dt, end_date_dt, "Hotel Calendar don't end in the correct date!")

                    for k_price, v_price in enumerate(self.prices_tmp[vroom_pr['room']]):
                        self.assertEqual(v_price, vroom_pr['days'][sorted_dates[k_price+1]], "Hotel Calendar Pricelist doesn't match!")

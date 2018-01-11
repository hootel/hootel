# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
from datetime import datetime, timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
import pytz
import logging
_logger = logging.getLogger(__name__)


class TestManagementCalendar(TestHotelCalendar):

    def test_calendar_prices(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['prices'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        if k_info >= len(self.prices_tmp[vroom.id]):
                            break
                        self.assertEqual(v_info['price'], self.prices_tmp[vroom.id][k_info], "Hotel Calendar Management Prices doesn't match!")

        # REMOVE PRICES
        pr_ids = self.env['product.pricelist.item'].sudo(self.user_hotel_manager).search([
            ('pricelist_id', '=', self.parity_pricelist_id),
            ('product_tmpl_id', 'in', (self.hotel_vroom_budget.product_id.product_tmpl_id.id, self.hotel_vroom_special.product_id.product_tmpl_id.id)),
        ])
        pr_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        self.assertFalse(any(hcal_data['prices']), "Hotel Calendar Management Prices doesn't match after remove!")

    def test_calendar_restrictions(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['restrictions'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        if k_info >= len(self.restrictions_min_stay_tmp[vroom.id]):
                            break
                        self.assertEqual(v_info['min_stay'], self.restrictions_min_stay_tmp[vroom.id][k_info], "Hotel Calendar Management Restrictions doesn't match!")

        # REMOVE RESTRICTIONS
        rest_ids = self.env['hotel.virtual.room.restriction.item'].sudo(self.user_hotel_manager).search([
            ('applied_on', '=', '0_virtual_room'),
            ('restriction_id', '=', self.parity_restrictions_id),
            ('virtual_room_id', 'in', (self.hotel_vroom_budget.id, self.hotel_vroom_special.id)),
        ])
        rest_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        self.assertFalse(any(hcal_data['restrictions']), "Hotel Calendar Management Restrictions doesn't match after remove!")

    def test_calendar_availability(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        if k_info >= len(self.avails_tmp[vroom.id]):
                            break
                        self.assertEqual(v_info['avail'], self.avails_tmp[vroom.id][k_info], "Hotel Calendar Management Availability doesn't match!")

        # REMOVE RESTRICTIONS
        avail_ids = self.env['hotel.virtual.room.availabity'].sudo(self.user_hotel_manager).search([
            ('virtual_room_id', 'in', (self.hotel_vroom_budget.id, self.hotel_vroom_special.id)),
        ])
        avail_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['avail'], vroom.max_real_rooms, "Hotel Calendar Management Availability doesn't match!")

    def test_save_changes(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=3)
        hotel_calendar_management_obj = self.env['hotel.calendar.management']
        vrooms = (self.hotel_vroom_budget,)

        # Generate new prices
        prices = (144.0, 170.0, 30.0, 50.0)
        cprices = {}
        for k_item, v_item in enumerate(prices):
            ndate = now_utc_dt + timedelta(days=k_item)
            cprices.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'price': v_item
            })

        # Generate new restrictions
        restrictions = {
            'min_stay': (3, 2, 4, 1),
            'max_stay': (5, 8, 9, 3),
            'min_stay_arrival': (2, 3, 6, 2),
            'closed_departure': (False, True, False, True),
            'closed_arrival': (True, False, False, False),
            'closed': (False, False, True, True),
        }
        crestrictions = {}
        for i in range(0, 4):
            ndate = now_utc_dt + timedelta(days=i)
            crestrictions.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'closed_arrival': restrictions['closed_arrival'][i],
                'max_stay': restrictions['max_stay'][i],
                'min_stay': restrictions['min_stay'][i],
                'closed_departure': restrictions['closed_departure'][i],
                'closed': restrictions['closed'][i],
                'min_stay_arrival': restrictions['min_stay_arrival'][i],
            })

        # Generate new availability
        avails = (1, 2, 2, 1)
        cavails = {}
        for k_item, v_item in enumerate(avails):
            ndate = now_utc_dt + timedelta(days=k_item)
            cavails.setdefault(self.hotel_vroom_budget.id, []).append({
                'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'avail': v_item,
                'no_ota': False,
            })

        # Save new values
        hotel_calendar_management_obj.sudo(self.user_hotel_manager).save_changes(
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            cprices,
            crestrictions,
            cavails)

        # Check data integrity
        hcal_data = hotel_calendar_management_obj.sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)

        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['avail'], avails[k_info], "Hotel Calendar Management Availability doesn't match!")
            for k_pr, v_pr in hcal_data['restrictions'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['min_stay'], restrictions['min_stay'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
                        self.assertEqual(v_info['max_stay'], restrictions['max_stay'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
                        self.assertEqual(v_info['min_stay_arrival'], restrictions['min_stay_arrival'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
                        self.assertEqual(v_info['closed_departure'], restrictions['closed_departure'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
                        self.assertEqual(v_info['closed_arrival'], restrictions['closed_arrival'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
                        self.assertEqual(v_info['closed'], restrictions['closed'][k_info], "Hotel Calendar Management Restrictions doesn't match!")
            for k_pr, v_pr in hcal_data['prices'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['price'], prices[k_info], "Hotel Calendar Management Prices doesn't match!")

    def test_calendar_reservations(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_special,)

        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio, reservation = self.create_reservation(
            self.user_hotel_manager,
            self.partner_2,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restrictions_id,
            True)

        reserv_start_dt = reserv_start_utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.tz_hotel))
        reserv_end_dt = reserv_end_utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.tz_hotel))
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['count_reservations'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        ndate = datetime.strptime(v_info['date'], DEFAULT_SERVER_DATE_FORMAT).replace(tzinfo=pytz.timezone(self.tz_hotel))
                        if ndate >= reserv_start_dt and ndate <= reserv_end_dt:
                            self.assertEqual(v_info['num'], vroom.total_rooms_count-1, "Hotel Calendar Management Availability doesn't match!")

    def test_invalid_input_calendar_data(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                False,
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                False,
                self.parity_pricelist_id,
                self.parity_restrictions_id,
                True)
        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            False,
            False,
            True)
        self.assertTrue(any(hcal_data), "Hotel Calendar invalid default management parity models!")

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

    def test_calendar_prices(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restriction_id,
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
            self.parity_restriction_id,
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
            self.parity_restriction_id,
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
            ('restriction_id', '=', self.parity_restriction_id),
            ('virtual_room_id', 'in', (self.hotel_vroom_budget.id, self.hotel_vroom_special.id)),
        ])
        rest_ids.sudo(self.user_hotel_manager).unlink()

        hcal_data = self.env['hotel.calendar.management'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
            self.parity_pricelist_id,
            self.parity_restriction_id,
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
            self.parity_restriction_id,
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
            self.parity_restriction_id,
            True)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['availability'].iteritems():
                if k_pr == vroom.id: # Only Check Test Cases
                    for k_info, v_info in enumerate(v_pr):
                        self.assertEqual(v_info['avail'], vroom.max_real_rooms, "Hotel Calendar Management Availability doesn't match!")

    def test_save_changes(self):
        _logger.info("IMPLEMENT ME")

    def test_calendar_reservations(self):
        _logger.info("IMPLEMENT ME")

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

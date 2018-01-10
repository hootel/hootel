# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import ValidationError
from .common import TestHotelCalendar
import logging
_logger = logging.getLogger(__name__)


class TestReservationsCalendar(TestHotelCalendar):

    def test_calendar_pricelist(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        real_start_utc_dt = (now_utc_dt - timedelta(days=1))
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
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

        # Check Pricelist Integrity after unlink
        pr_ids = self.env['product.pricelist.item'].sudo(self.user_hotel_manager).search([
            ('pricelist_id', '=', self.parity_pricelist_id),
            ('product_tmpl_id', 'in', (self.hotel_vroom_budget.product_id.product_tmpl_id.id, self.hotel_vroom_special.product_id.product_tmpl_id.id)),
        ])
        pr_ids.sudo(self.user_hotel_manager).unlink()
        hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
            now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            [], [])
        vrooms = (self.hotel_vroom_budget, self.hotel_vroom_special)
        for vroom in vrooms:
            for k_pr, v_pr in hcal_data['pricelist'].iteritems():
                for vroom_pr in v_pr:
                    if vroom_pr['room'] == vroom.id: # Only Check Test Cases
                        self.assertEqual(vroom.list_price, vroom_pr['days'][sorted_dates[k_price+1]], "Hotel Calendar Pricelist doesn't match after remove!")

    def test_calendar_reservations(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        def is_reservation_listed(reservation_id):
            hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                [], [])
            # TODO: Perhaps not the best way to do this test... :/
            hasReservationTest = False
            for reserv in hcal_data['reservations']:
                if reserv[1] == reservation_id:
                    hasReservationTest = True
                    break
            return hasReservationTest

        # CREATE COMPLETE RESERVATION (3 Nigths)
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
        folio, reservation = self.create_reservation(
            self.user_hotel_manager,
            self.partner_2,
            reserv_start_utc_dt,
            reserv_end_utc_dt,
            self.hotel_room_double_200,
            "Reservation Test #1")

        # CHECK SUCCESSFULL CREATION
        self.assertTrue(is_reservation_listed(reservation.id), "Hotel Calendar can't found test reservation!")

        # CONFIRM FOLIO
        folio.sudo(self.user_hotel_manager).action_confirm()
        self.assertTrue(is_reservation_listed(reservation.id), "Hotel Calendar can't found test reservation!")

        # CANCEL FOLIO
        folio.sudo(self.user_hotel_manager).action_cancel()
        self.assertFalse(is_reservation_listed(reservation.id), "Hotel Calendar can't found test reservation!")

        # REMOVE FOLIO
        folio.sudo().unlink()   # FIXME: Can't use: self.user_hotel_manager ?¿?!???
        self.assertFalse(is_reservation_listed(reservation.id), "Hotel Calendar can't found test reservation!")

    def test_invalid_input_calendar_data(self):
        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        adv_utc_dt = now_utc_dt + timedelta(days=15)

        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                [], [])
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                False,
                [], [])
        with self.assertRaises(ValidationError):
            hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
                False,
                False,
                [], [])

    def test_calendar_settings(self):
        hcal_options = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_settings()

        self.assertEqual(hcal_options['divide_rooms_by_capacity'], True, "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['eday_week'], 6, "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['days'], 'month', "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['allow_invalid_actions'], False, "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['assisted_movement'], False, "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['default_arrival_hour'], '14:00', "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['default_departure_hour'], '12:00', "Hotel Calendar Invalid Options!")
        self.assertEqual(hcal_options['show_notifications'], True, "Hotel Calendar Invalid Options!")

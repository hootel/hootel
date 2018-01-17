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
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from openerp.exceptions import ValidationError
from .common import TestHotelWubook
from odoo.addons.hotel import date_utils
import pytz
import logging
_logger = logging.getLogger(__name__)


class TestWubook(TestHotelWubook):

    def test_simple_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],   # 1 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreserv = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertTrue(nreserv, "Reservation not found")
        self.assertEqual(nreserv.state, 'draft', "Invalid reservation state")
        nfolio = self.env['hotel.folio'].search([
            ('id', '=', nreserv.folio_id.id)
        ], limit=1)
        self.assertTrue(nfolio, "Folio not found")
        self.assertEqual(nfolio.state, 'draft', "Invalid folio state")

        # Check Dates
        self.assertEqual(
            nreserv.checkin,
            checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "Invalid Checkin Reservation Date")
        self.assertEqual(
            nreserv.checkout,
            checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "Invalid Checkout Reservation Date")
        # Check Price
        self.assertEqual(nreserv.price_unit, 30.0, "Invalid Reservation Price")
        # Check Reservation Lines
        self.assertTrue(any(nreserv.reservation_lines),
                        "Reservation lines snot found")
        dates_arr = date_utils.generate_dates_list(checkin_dt, date_diff-1)
        for k_line, v_line in enumerate(nreserv.reservation_lines):
            self.assertEqual(dates_arr[k_line], v_line['date'],
                             "Invalid Reservation Lines Dates")

    def test_complex_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1, 1],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)

        # Check Creation
        self.assertTrue(any(processed_rids), "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertEqual(len(nreservs), 2, "Reservations not found")

        for nreserv in nreservs:
            self.assertEqual(nreserv.state, 'draft',
                             "Invalid reservation state")

            # Check Dates
            self.assertEqual(
                nreserv.checkin,
                checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "Invalid Checkin Reservation Date")
            self.assertEqual(
                nreserv.checkout,
                checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "Invalid Checkout Reservation Date")
            # Check Price
            self.assertEqual(nreserv.price_unit, 30.0,
                             "Invalid Reservation Price")
            # Check Reservation Lines
            self.assertTrue(any(nreserv.reservation_lines),
                            "Reservation lines snot found")
            dates_arr = date_utils.generate_dates_list(checkin_dt, date_diff-1)
            for k_line, v_line in enumerate(nreserv.reservation_lines):
                self.assertEqual(dates_arr[k_line], v_line['date'],
                                 "Invalid Reservation Lines Dates")

    def test_complex_bookings(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt - timedelta(days=3)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt + timedelta(days=3)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            )
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 3, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

    def test_cancel_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        def check_state(wrids, state):
            reservs = self.env['hotel.reservation'].sudo().search([
                    ('wrid', 'in', wrids)
                ])
            self.assertTrue(any(reservs), "Reservations not found")
            for reserv in reservs:
                self.assertEqual(
                        reserv.state, state, "Reservation state invalid")

        # Create Reservation
        nbook = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_special.wrid: {
                    'occupancy': [2],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            })
        wbooks = [nbook]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        # Cancel It
        wbooks = [self.cancel_booking(nbook)]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        check_state(processed_rids, 'cancelled')

        # Create Reservation and Cancel It
        nbook = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_special.wrid: {
                    'occupancy': [2],   # 2 Reservation Line
                    'dayprices': [15.0, 15.0]   # 2 Days
                }
            })
        cbook = self.cancel_booking(nbook)
        wbooks = [nbook, cbook]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        _logger.info(processed_rids)
        self.assertEqual(len(processed_rids), 2, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        check_state(processed_rids, 'cancelled')

    def test_splitted_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        book_a = self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )
        book_b = self.create_wubook_booking(
            self.user_hotel_manager,
            (checkin_dt + timedelta(days=3)).strftime(
                                        DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )
        wbooks = [book_a, book_b]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 2, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")
        reserv = self.env['hotel.reservation'].search([
            ('wrid', '=', book_b['reservation_code'])
        ], limit=1)
        self.assertTrue(reserv, "Rervation doesn't exists")
        self.assertEqual(
            reserv.product_id.id,
            self.hotel_room_simple_100.product_id.id,
            "Unexpected room assigned")
        reserv.product_id = \
            self.hotel_room_simple_101.product_id.id

        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_budget.wrid: {
                        'occupancy': [1],
                        'dayprices': [15.0, 15.0, 20.0, 17.0]
                    }
                }
            )
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Reservation not found")
        self.assertFalse(errors, "Reservation errors")

        # Check Splitted Integrity
        nreservs = self.env['hotel.reservation'].search([
            ('wrid', 'in', processed_rids)
        ])
        self.assertEqual(len(nreservs), 2, "Reservations not found")
        date_dt = date_utils.get_datetime(nreservs[0].checkin)
        self.assertEqual(nreservs[0].reservation_lines[0].date,
                         date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Invalid split")
        date_dt = date_utils.get_datetime(nreservs[1].checkin)
        self.assertEqual(nreservs[1].reservation_lines[0].date,
                         date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                         "Invalid split")
        self.assertEqual(nreservs[0].price_unit,
                         30.0,
                         "Invalid split price")
        self.assertEqual(nreservs[1].price_unit,
                         37.0,
                         "Invalid split price")
        self.assertEqual(nreservs[1].parent_reservation.id,
                         nreservs[0].id,
                         "Invalid split parent reservation")
        self.assertEqual(nreservs[0].product_id.id,
                         self.hotel_room_simple_101.product_id.id,
                         "Invalid room assigned")
        self.assertEqual(nreservs[1].product_id.id,
                         self.hotel_room_simple_100.product_id.id,
                         "Invalid room assigned")

    def test_invalid_booking(self):
        now_utc_dt = date_utils.now()
        checkin_utc_dt = now_utc_dt + timedelta(days=3)
        checkin_dt = date_utils.dt_as_timezone(checkin_utc_dt,
                                               self.tz_hotel)
        checkout_utc_dt = checkin_utc_dt + timedelta(days=2)
        date_diff = date_utils.date_diff(checkin_utc_dt, checkout_utc_dt,
                                         hours=False) + 1

        # Invalid Occupancy
        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_budget.wrid: {
                    'occupancy': [3],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(errors, "Invalid reservation created")
        self.assertFalse(any(processed_rids), "Invalid reservation created")

        # No Real Rooms Avail
        wbooks = [self.create_wubook_booking(
            self.user_hotel_manager,
            checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            self.partner_2,
            {
                self.hotel_vroom_special.wrid: {
                    'occupancy': [2, 1],
                    'dayprices': [15.0, 15.0]
                }
            }
        )]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertTrue(errors, "Invalid reservation created")
        self.assertFalse(any(processed_rids), "Invalid reservation created")

        # No Real Rooms Avail
        wbooks = [
            self.create_wubook_booking(
                self.user_hotel_manager,
                checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt - timedelta(days=1)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
            self.create_wubook_booking(
                self.user_hotel_manager,
                (checkin_dt + timedelta(days=1)).strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                self.partner_2,
                {
                    self.hotel_vroom_special.wrid: {
                        'occupancy': [2],   # 2 Reservation Line
                        'dayprices': [15.0, 15.0]   # 2 Days
                    }
                }
            ),
        ]
        processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
            self.env['wubook'].sudo().generate_reservations(wbooks)
        self.assertEqual(len(processed_rids), 1, "Invalid Reservation created")
        self.assertTrue(errors, "Invalid Reservation created")

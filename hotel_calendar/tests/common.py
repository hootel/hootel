# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
from odoo import fields
from odoo.addons.hotel.tests.common import TestHotel
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta
import pytz


class TestHotelCalendar(TestHotel):

    @classmethod
    def setUpClass(cls):
        super(TestHotelCalendar, cls).setUpClass()

        now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # CREATE COMPLETE RESERVATION (3 Nigths)
        reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
        reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)

        # Create Folio
        cls.folio_1 = cls.env['hotel.folio'].create({
            'partner_id': cls.partner_2.id,
        })

        # Create Reservation (Special Room)
        cls.reservation_1 = cls.env['hotel.reservation'].create({
            'name': 'Reservation Test #1',
            'adults': 1,
            'children': 0,
            'checkin': reserv_start_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'checkout': reserv_end_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'folio_id': cls.folio_1.id,
            'product_id': cls.hotel_room_double_200.product_id.id,
        })

        # Create Reservation Lines + Update Reservation Price
        # Used replace for flag datetime object as UTC (required for time-zone conversions)
        reserv_start_dt = reserv_start_utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(cls.tz_hotel))
        reserv_end_dt = reserv_end_utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(cls.tz_hotel))
        days_diff = abs((reserv_end_dt - reserv_start_dt).days-1)
        res = cls.reservation_1.prepare_reservation_lines(reserv_start_dt, days_diff)
        cls.reservation_1.write({
            'reservation_lines': res['commands'],
            'price_unit': res['total_price'],
        })

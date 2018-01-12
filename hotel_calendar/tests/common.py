# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
from odoo.addons.hotel.tests.common import TestHotel


class TestHotelCalendar(TestHotel):

    @classmethod
    def setUpClass(cls):
        super(TestHotelCalendar, cls).setUpClass()

        # Minimal Hotel Calendar Configuration
        cls.tz_hotel = 'Europe/Madrid'
        cls.parity_pricelist_id = cls.pricelist_1.id
        cls.parity_restrictions_id = cls.restriction_1.id
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'divide_rooms_by_capacity', True)
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'type_move', 'normal')
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'end_day_week', 6)
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_num_days', 'month')
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_arrival_hour', '14:00')
        cls.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_departure_hour', '12:00')

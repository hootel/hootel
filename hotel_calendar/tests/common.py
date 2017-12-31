# -*- coding: utf-8 -*-

from odoo import api
from odoo.tests import common

class TestCalendar(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestCalendar, cls).setUpClass()

        # Create Tests Records
        RoomTypes = cls.env['hotel.room.type']
        cls.hotel_room_type_simple = RoomTypes.create({
            'name': 'Simple',
            'code_type': 'SMP',
        })
        cls.hotel_room_type_double = RoomTypes.create({
            'name': 'Double',
            'code_type': 'DBL',
        })

        VRooms = cls.env['hotel.virtual.room']
        cls.hotel_vroom_budget = VRooms.create({
            'name': 'Budget Room',
            'virtual_code': '001',
            'list_price': 50,
        })
        cls.hotel_vroom_special = VRooms.create({
            'name': 'Special Room',
            'virtual_code': '002',
            'list_price': 150,
        })

        Rooms = cls.env['hotel.room']
        cls.hotel_room_simple_100 = Rooms.create({
            'name': '100',
            'sale_price_type': 'vroom',
            'price_virtual_room': cls.hotel_vroom_budget.id,
            'categ_id': cls.hotel_room_type_simple.id,
        })
        cls.hotel_room_simple_101 = Rooms.create({
            'name': '101',
            'sale_price_type': 'vroom',
            'price_virtual_room': cls.hotel_vroom_budget.id,
            'categ_id': cls.hotel_room_type_simple.id,
        })
        cls.hotel_room_simple_200 = Rooms.create({
            'name': '200',
            'sale_price_type': 'vroom',
            'price_virtual_room': cls.hotel_vroom_special.id,
            'categ_id': cls.hotel_room_type_double.id,
        })

        cls.hotel_vroom_budget.write({
            'room_ids': [(0, False, [cls.hotel_room_simple_100.id, cls.hotel_room_simple_101.id])],
            'max_real_rooms': 2,
        })
        cls.hotel_vroom_special.write({
            'room_ids': [(0, False, [cls.hotel_room_simple_200.id])],
            'max_real_rooms': 1,
        })

        # TODO: Crear disponibilidad, restricciones y precios (15 días desde el actual)
        # FIXME: Igual mejor mover esta clase al modulo de 'hotel' y herederar

# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
from datetime import timedelta
from odoo import api, fields
from odoo.tests import common
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.mail.tests.common import TestMail
import pytz


# TestMail crea recursos utiles para nuestros test... por ejemplo, usuarios con distintos tipos de nivel, etc...
class TestHotel(TestMail):

    def create_reservation(self, creator, partner, checkin, checkout, room, resname, adults=1, children=0):
        # Create Folio
        folio = self.env['hotel.folio'].sudo(creator).create({
            'partner_id': partner.id,
        })
        self.assertTrue(folio, "Hotel Calendar can't create folio for new reservation!")

        # Create Reservation (Special Room)
        reservation = self.env['hotel.reservation'].sudo(creator).create({
            'name': resname,
            'adults': adults,
            'children': children,
            'checkin': checkin.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'checkout': checkout.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'folio_id': folio.id,
            'order_id.parter_id': partner.id,
            'product_id': room.product_id.id,
        })
        self.assertTrue(reservation, "Hotel Calendar can't create a new reservation!")

        # Create Reservation Lines + Update Reservation Price
        # Used replace for flag datetime object as UTC (required for time-zone conversions)
        reserv_start_dt = checkin.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.tz_hotel))
        reserv_end_dt = checkout.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.tz_hotel))
        days_diff = abs((reserv_end_dt - reserv_start_dt).days-1)
        res = reservation.sudo(creator).prepare_reservation_lines(reserv_start_dt, days_diff)
        reservation.sudo(creator).write({
            'reservation_lines': res['commands'],
            'price_unit': res['total_price'],
        })

        return (folio, reservation)


    @classmethod
    def setUpClass(cls):
        super(TestHotel, cls).setUpClass()

        # Hotel Time-Zone
        cls.tz_hotel = cls.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel') or 'UTC'

        # Parity models
        cls.parity_pricelist_id = int(cls.env['ir.values'].get_default('hotel.config.settings', 'parity_pricelist_id'))
        cls.parity_restriction_id = int(cls.env['ir.values'].get_default('hotel.config.settings', 'parity_restrictions_id'))

        # User Groups
        user_group_hotel_manager = cls.env.ref('hotel.group_hotel_manager')
        user_group_hotel_user = cls.env.ref('hotel.group_hotel_user')
        user_group_employee = cls.env.ref('base.group_user')
        user_group_public = cls.env.ref('base.group_public')
        user_group_account_invoice = cls.env.ref('account.group_account_invoice')

        # Create Test Users
        Users = cls.env['res.users'].with_context({'no_reset_password': True, 'mail_create_nosubscribe': True})
        cls.user_hotel_manager = Users.create({
            'name': 'Jeff Hotel Manager',
            'login': 'hoteljeff',
            'email': 'mynameisjeff@example.com',
            'signature': '--\nJeff',
            'notify_email': 'always',
            'groups_id': [(6, 0, [user_group_hotel_manager.id, user_group_employee.id, user_group_account_invoice.id])]})
        cls.user_hotel_user = Users.create({
            'name': 'Juancho Hotel User',
            'login': 'juancho',
            'email': 'juancho@example.com',
            'signature': '--\nJuancho',
            'notify_email': 'always',
            'groups_id': [(6, 0, [user_group_hotel_user.id, user_group_public.id])]})


        # Create Tests Records
        RoomTypes = cls.env['hotel.room.type']
        cls.hotel_room_type_simple = RoomTypes.create({
            'name': 'Simple',
            'code_type': 'TSMP',
        })
        cls.hotel_room_type_double = RoomTypes.create({
            'name': 'Double',
            'code_type': 'TDBL',
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
            'categ_id': cls.hotel_room_type_simple.cat_id.id,
        })
        cls.hotel_room_simple_101 = Rooms.create({
            'name': '101',
            'sale_price_type': 'vroom',
            'price_virtual_room': cls.hotel_vroom_budget.id,
            'categ_id': cls.hotel_room_type_simple.cat_id.id,
        })
        cls.hotel_room_double_200 = Rooms.create({
            'name': '200',
            'sale_price_type': 'vroom',
            'price_virtual_room': cls.hotel_vroom_special.id,
            'categ_id': cls.hotel_room_type_double.cat_id.id,
        })

        cls.hotel_vroom_budget.write({
            'room_ids': [(6, False, [cls.hotel_room_simple_100.id, cls.hotel_room_simple_101.id])],
        })
        cls.hotel_vroom_special.write({
            'room_ids': [(6, False, [cls.hotel_room_double_200.id])],
        })

        # Create a week of fresh data
        now_utc_dt = fields.datetime.now()
        cls.avails_tmp = {
            cls.hotel_vroom_budget.id: (1, 2, 2, 1, 1, 2, 2),
            cls.hotel_vroom_special.id: (1, 1, 1, 1, 1, 1, 1),
        }
        product_tmpl_ids = {
            cls.hotel_vroom_budget.id: cls.hotel_vroom_budget.product_id.product_tmpl_id.id,
            cls.hotel_vroom_special.id: cls.hotel_vroom_special.product_id.product_tmpl_id.id,
        }
        cls.prices_tmp = {
            cls.hotel_vroom_budget.id: (10.0, 80.0, 80.0, 95.0, 90.0, 80.0, 20.0),
            cls.hotel_vroom_special.id: (5.0, 15.0, 15.0, 35.0, 35.0, 10.0, 10.0),
        }
        vroom_avail_obj = cls.env['hotel.virtual.room.availabity']
        vroom_rest_item_obj = cls.env['hotel.virtual.room.restriction.item']
        pricelist_item_obj = cls.env['product.pricelist.item']
        for k_vr, v_vr in cls.avails_tmp.iteritems():
            for i in range(0, len(v_vr)):
                ndate = now_utc_dt + timedelta(days=i)
                vroom_avail_obj.create({
                    'virtual_room_id': k_vr,
                    'avail': v_vr[i],
                    'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                })
                vroom_rest_item_obj.create({
                    'virtual_room_id': k_vr,
                    'restriction_id': cls.parity_restriction_id,
                    'date_start': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'applied_on': '0_virtual_room',
                })
                pricelist_item_obj.create({
                    'pricelist_id': cls.parity_pricelist_id,
                    'date_start': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'compute_price': 'fixed',
                    'applied_on': '1_product',
                    'product_tmpl_id': product_tmpl_ids[k_vr],
                    'fixed_price': cls.prices_tmp[k_vr][i],
                })

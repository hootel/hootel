# -*- coding: utf-8 -*-
# Created by Alexandre Díaz <dev@redneboa.es>
import datetime
from datetime import timedelta
from odoo import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.hotel.tests.common import TestHotel
import logging
_logger = logging.getLogger(__name__)


class TestReservationsCalendar(TestHotel):

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

    # def test_calendar_reservations(self):
    #     now_utc_dt = fields.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    #     adv_utc_dt = now_utc_dt + timedelta(days=15)
    #
    #     # CREATE COMPLETE RESERVATION (3 Nigths)
    #     reserv_start_utc_dt = now_utc_dt + timedelta(days=3)
    #     reserv_end_utc_dt = reserv_start_utc_dt + timedelta(days=3)
    #     folio, reservation = self.create_reservation(
    #         self.user_hotel_manager,
    #         self.partner_2,
    #         reserv_start_utc_dt,
    #         reserv_end_utc_dt,
    #         self.hotel_room_double_200,
    #         "Reservation Test #1")
    #
    #     hcal_data = self.env['hotel.reservation'].sudo(self.user_hotel_manager).get_hcalendar_all_data(
    #         now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #         adv_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #         [], [])
    #     self.assertTrue(any(hcal_data['reservations']), "Hotel Calendar don't receive any reservation, more than 1 expected...")
    #
    #     # TODO: Perhaps not the best way to do this test... :/
    #     hasReservationTest = False
    #     for reserv in hcal_data['reservations']:
    #         if reserv[1] == reservation.id:
    #             hasReservationTest = True
    #             break
    #     self.assertTrue(hasReservationTest, "Hotel Calendar can't found test reservation!")

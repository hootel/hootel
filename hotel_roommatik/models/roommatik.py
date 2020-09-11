# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime, timedelta
from odoo import api, models, fields
# from odoo.tools import (
#     DEFAULT_SERVER_DATE_FORMAT,
#     DEFAULT_SERVER_DATETIME_FORMAT)
import logging
_logger = logging.getLogger(__name__)

DEFAULT_ROOMMATIK_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_ROOMMATIK_TIME_FORMAT = "%H:%M:%S"
DEFAULT_ROOMMATIK_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_ROOMMATIK_DATE_FORMAT,
    DEFAULT_ROOMMATIK_TIME_FORMAT)


class RoomMatik(models.Model):
    _name = 'roommatik.api'

    @api.model
    def rm_get_date(self):
        # RoomMatik API Gets the current business date/time. (MANDATORY)
        _logger.info('---------------------------ROOMMATIK: rm_get_date')
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        self_tz = self.with_context(tz=tz_hotel)
        mynow = fields.Datetime.context_timestamp(self_tz, datetime.now()).\
            strftime(DEFAULT_ROOMMATIK_DATETIME_FORMAT)
        json_response = {
            'dateTime': mynow
            }
        json_response = json.dumps(json_response)
        _logger.info('---------------------------RETURN:')
        _logger.info(json_response)
        return json_response

    @api.model
    def rm_get_reservation(self, reservation_code):
        _logger.info('---------------------------ROOMMATIK: rm_get_reservation')
        _logger.info('PARAM reservation_code:')
        _logger.info(reservation_code)
        # RoomMatik Gets a reservation ready for check-in
        # through the provided code. (MANDATORY)
        apidata = self.env['hotel.reservation']
        reservation_code = str(reservation_code) if not isinstance(
            reservation_code, str) else reservation_code
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_get_reservation(reservation_code)
        _logger.info(response)
        return response

    @api.model
    def rm_add_customer(self, customer):
        _logger.info('---------------------------ROOMMATIK: rm_add_customer')
        _logger.info('PARAM customer:')
        _logger.info(customer)
        # RoomMatik API Adds a new PMS customer through the provided parameters
        # Addition will be ok if the returned customer has ID. (MANDATORY)
        apidata = self.env['res.partner']
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_add_customer(customer)
        _logger.info(response)
        return response

    @api.model
    def rm_checkin_partner(self, stay):
        # RoomMatik API Check-in a stay.
        # Addition will be ok if the returned stay has ID. (MANDATORY)
        _logger.info('---------------------------ROOMMATIK: rm_checkin_partner')
        _logger.info('PARAM stay:')
        _logger.info (stay)
        apidata = self.env['hotel.checkin.partner']
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_checkin_partner(stay)
        _logger.info(response)
        return response

    @api.model
    def rm_get_stay(self, check_in_code):
        # RoomMatik API  Gets stay information through check-in code
        # (if code is related to a current stay)
        # (MANDATORY for check-out kiosk)
        _logger.info('---------------------------ROOMMATIK: rm_get_stay')
        _logger.info('PARAM check_in_code:')
        _logger.info(check_in_code)
        apidata = self.env['hotel.checkin.partner']
        check_in_code = str(check_in_code) if not isinstance(
            check_in_code, str) else check_in_code
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_get_stay(check_in_code)
        _logger.info(response)
        return response

    @api.model
    def rm_get_all_room_type_rates(self):
        # Gets the current room rates and availability. (MANDATORY)
        # return ArrayOfRoomTypeRate
        _logger.info('---------------------------ROOMMATIK: rm_get_all_room_type_rates')
        apidata = self.env['hotel.room.type']
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_get_all_room_type_rates()
        _logger.info(response)
        return response

    @api.model
    def rm_get_prices(self, start_date, number_intervals, room_type, guest_number):
        # Gets some prices related to different dates of the same stay.
        # return ArrayOfDecimal
        _logger.info('---------------------------ROOMMATIK: rm_get_prices')
        _logger.info('start_date: ' + str(start_date) + ', number_intervals: ' + str(number_intervals) + ', room_type: ' + str(room_type) + ', guest_number:' + str(guest_number))
        apidata = self.env['hotel.room.type']
        room_type = apidata.browse(int(room_type))
        if not room_type:
            return {'State': 'Error Room Type not Found'}
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_get_prices(start_date, number_intervals, room_type, guest_number)
        _logger.info(response)
        return response

    @api.model
    def rm_get_segmentation(self):
        # Gets segmentation list
        # return ArrayOfSegmentation
        _logger.info('---------------------------ROOMMATIK: rm_Get_segmentation')
        segmentations = self.env['res.partner.category'].sudo().search([])
        response = []
        for segmentation in segmentations:
            response.append({
                "Segmentation": {
                    "Id": segmentation.id,
                    "Name": segmentation.display_name,
                    },
                })
            json_response = json.dumps(response)
        _logger.info('---------------------------RETURN:')
        _logger.info(json_response)
        return json_response

    @api.model
    def rm_add_payment(self, code, payment):
        _logger.info('---------------------------ROOMMATIK: rm_add_payment')
        _logger.info('code: ' + str(code) + ', payment: ' + str(payment))
        apidata = self.env['account.payment']
        code = str(code) if not isinstance(code, str) else code
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_add_payment(code, payment)
        _logger.info(response)
        return response

    @api.model
    def rm_get_departures(self):
        _logger.info('---------------------------ROOMMATIK: rm_get_departures')
        apidata = self.env['hotel.reservation']
        response = apidata.sudo().rm_get_departures()
        _logger.info(response)
        return response

    @api.model
    def rm_get_arrivals(self):
        _logger.info('---------------------------ROOMMATIK: rm_get_arrivals')
        apidata = self.env['hotel.reservation']
        _logger.info('---------------------------RETURN:')
        response = apidata.sudo().rm_get_arrivals()
        _logger.info(response)
        return response

    def normalize_checkin_date(self, date_in, date_out):
        # Adjust reservation day to night sale kiosk
        limit_night_sale = self.env.user.company_id.limit_night_sale
        start_night_sale = datetime.strptime('00:00', '%H:%M').time()
        limit_sale_today = datetime.strptime(limit_night_sale, '%H:%M').time()
        checkin = datetime.strptime(date_in, DEFAULT_ROOMMATIK_DATE_FORMAT)
        checkout = datetime.strptime(date_out, DEFAULT_ROOMMATIK_DATE_FORMAT)
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        self_tz = self.with_context(tz=tz_hotel)
        mynow = fields.Datetime.context_timestamp(
            self_tz,
            datetime.now())
        if start_night_sale < mynow.time() < limit_sale_today and \
                checkin.date() == mynow.date():
            checkin = checkin - timedelta(1)
            checkout = checkout - timedelta(1)
        return checkin.strftime(DEFAULT_ROOMMATIK_DATE_FORMAT), checkout.strftime(DEFAULT_ROOMMATIK_DATE_FORMAT)

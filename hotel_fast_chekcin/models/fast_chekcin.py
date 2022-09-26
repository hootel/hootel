# Copyright 2020 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime
from odoo import api, models, fields
# from odoo.tools import (
#     DEFAULT_SERVER_DATE_FORMAT,
#     DEFAULT_SERVER_DATETIME_FORMAT)
import logging
_logger = logging.getLogger(__name__)

DEFAULT_FASTCHECKIN_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_FASTCHECKIN_TIME_FORMAT = "%H:%M:%S"
DEFAULT_FASTCHECKIN_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_FASTCHECKIN_DATE_FORMAT,
    DEFAULT_FASTCHECKIN_TIME_FORMAT)


class FastCheckin(models.Model):
    _name = 'fastcheckin.api'

    @api.model
    def fc_get_date(self):
        # FastCheckin API Gets the current business date/time. (MANDATORY)
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        self_tz = self.with_context(tz=tz_hotel)
        mynow = fields.Datetime.context_timestamp(self_tz, datetime.now()).\
            strftime(DEFAULT_FASTCHECKIN_DATETIME_FORMAT)
        json_response = {
            'serverTime': mynow
            }
        json_response = json.dumps(json_response)
        return json_response

    @api.model
    def fc_get_reservation(self, reservation_code):
        # FastCheckin Gets a reservation ready for check-in
        # through the provided code. (MANDATORY)
        _logger.info('FASTCHECKIN get reservation [%s] Code.', reservation_code)

        apidata = self.env['hotel.reservation']
        reservation_code = str(reservation_code) if not isinstance(
            reservation_code, str) else reservation_code
        return apidata.sudo().fc_get_reservation(reservation_code)

    @api.model
    def fc_set_partner(self, partner):
        # FastCheckin Sets a partner and assing a check-in
        _logger.info('FASTCHECKIN set partner')

        apidata = self.env['res.partner']
        return apidata.sudo().fc_set_partner(partner)

    @api.model
    def fc_next_localizator(self, dias=60):
        # FastCheckin get next reservations and send localizator and state
        apidata = self.env['hotel.reservation']
        return apidata.sudo().fc_next_localizator(dias)

    @api.model
    def fc_add_payment(self, code, amount, journal='0', name='FastCheckin'):
        # FastCheckin add payment
        # code = reservation Id
        apidata = self.env['account.payment']
        return apidata.sudo().fc_add_payment(code, amount, int(journal), name)

    @api.model
    def fc_check_zip(self, zip_id):
        better = self.env['res.better.zip'].search([('name', '=', zip_id)],
                                                   limit=1)

        json_response = better.city if len(better) == 1 else False
        json_response = json.dumps(json_response)
        return json_response

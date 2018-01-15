# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from openerp import http
from openerp.http import request
import logging
from openerp.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class website_wubook(http.Controller):
    # Called when created a reservation in wubook
    @http.route(['/wubook/push/reservations/<string:security_token>'],
                type='http', cors="*", auth="public", methods=['POST'],
                website=True, csrf=False)
    def wubook_push_reservations(self, security_token, **kwargs):
        # Check Security Token
        hotel_security_token = request.env['ir.values'].sudo().get_default(
                        'wubook.config.settings', 'wubook_push_security_token')
        _logger.info("=== PUSH RR")
        _logger.info(security_token)
        _logger.info(hotel_security_token)
        if security_token != hotel_security_token:
            raise ValidationError('Invalid Security Token!')

        rcode = kwargs.get('rcode')
        lcode = kwargs.get('lcode')

        # Correct Input?
        if not lcode or not rcode:
            raise ValidationError('Invalid Input Parameters!')

        # WuBook Check
        if rcode == '2000' and lcode == '1000':
            return request.make_response(
                                    '200 OK', [('Content-Type', 'text/plain')])

        # Poor Security Check
        wlcode = request.env['ir.values'].sudo().get_default(
                                    'wubook.config.settings', 'wubook_lcode')
        if lcode != wlcode:
            raise ValidationError("Error! lcode doesn't match!")

        _logger.info("[WUBOOK] Importing Reservations...")
        # Create Reservation
        request.env['wubook'].sudo().fetch_booking(lcode, rcode)

        return request.make_response(
                                    '200 OK', [('Content-Type', 'text/plain')])

    # Called when modify room values (Delay: ~5mins)
    @http.route(['/wubook/push/rooms/<string:security_token>'], type='http',
                cors="*", auth="public", methods=['POST'], website=True,
                csrf=False)
    def wubook_push_rooms(self, security_token, **kwargs):
        # Check Security Token
        hotel_security_token = request.env['ir.values'].sudo().get_default(
                        'wubook.config.settings', 'wubook_push_security_token')
        _logger.info("=== PUSH RO")
        _logger.info(security_token)
        _logger.info(hotel_security_token)
        if security_token != hotel_security_token:
            raise ValidationError('Invalid Security Token!')

        lcode = kwargs.get('lcode')
        dfrom = kwargs.get('dfrom')
        dto = kwargs.get('dto')

        # Correct Input?
        if not lcode or not dfrom or not dto:
            raise ValidationError('Invalid Input Parameters!')

        # Poor Security Check
        wlcode = request.env['ir.values'].sudo().get_default(
                                    'wubook.config.settings', 'wubook_lcode')
        if lcode != wlcode:
            raise ValidationError("Error! lcode doesn't match!")

        _logger.info("[WUBOOK] Updating values...")
        wubook_obj = request.env['wubook'].sudo().with_context({
            'init_connection': False
        })
        if wubook_obj.init_connection():
            wubook_obj.fetch_rooms_values(dfrom, dto)
            wubook_obj.fetch_rplan_restrictions(dfrom, dto)
            parity_pricelist_id = self.env['ir.values'].sudo().get_default(
                                'hotel.config.settings', 'parity_pricelist_id')
            if parity_pricelist_id:
                pricelist_id = request.env['product.pricelist'].sudo().browse(
                                                    int(parity_pricelist_id))
                if pricelist_id and pricelist_id.wpid:
                    wubook_obj.fetch_plan_prices(pricelist_id.wpid, dfrom, dto)
            wubook_obj.close_connection()

        return request.make_response(
                                    '200 OK', [('Content-Type', 'text/plain')])

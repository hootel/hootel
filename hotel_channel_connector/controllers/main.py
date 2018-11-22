# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from openerp import http, _
from openerp.http import request
from openerp.exceptions import ValidationError
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)


class website_wubook(http.Controller):
    # Called when created a reservation in wubook
    @http.route(['/hotel_channel/push/reservations/<string:security_token>'],
                type='http', cors="*", auth="public", methods=['POST'],
                website=True, csrf=False)
    def wubook_push_reservations(self, security_token, **kwargs):
        rcode = kwargs.get('rcode')
        lcode = kwargs.get('lcode')

        # Correct Input?
        if not lcode or not rcode:
            raise ValidationError(_('Invalid Input Parameters!'))

        # WuBook Check
        if rcode == '2000' and lcode == '1000':
            return request.make_response('200 OK', [('Content-Type', 'text/plain')])

        # Get Backend
        backend = request.env['channel.backend'].search([
            ('security_token', '=', security_token),
            ('lcode', '=', lcode),
        ])
        if not backend:
            raise ValidationError(_("Can't found a backend!"))

        request.env['channel.hotel.reservation'].import_reservation(rcode)

        return request.make_response('200 OK', [('Content-Type', 'text/plain')])

    # Called when modify room values (Delay: ~5mins)
    @http.route(['/hotel_channel/push/rooms/<string:security_token>'], type='http',
                cors="*", auth="public", methods=['POST'], website=True,
                csrf=False)
    def wubook_push_rooms(self, security_token, **kwargs):
        lcode = kwargs.get('lcode')
        dfrom = kwargs.get('dfrom')
        dto = kwargs.get('dto')

        # Correct Input?
        if not lcode or not dfrom or not dto:
            raise ValidationError(_('Invalid Input Parameters!'))

        # Get Backend
        backend = request.env['channel.backend'].search([
            ('security_token', '=', security_token),
            ('lcode', '=', lcode),
        ])
        if not backend:
            raise ValidationError(_("Can't found a backend!"))

        odoo_dfrom = datetime.strptime(
            dfrom,
            DEFAULT_WUBOOK_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
        odoo_dto = datetime.strptime(
            dto,
            DEFAULT_WUBOOK_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)

        request.env['channel.hotel.room.type.availability'].import_availability(
            backend, odoo_dfrom, odoo_dto)
        request.env['channel.hotel.room.type.restriction.item'].import_restriction_values(
            backend, odoo_dfrom, odoo_dto, False)
        request.env['channel.product.pricelist.item'].import_pricelist_values(
            backend, odoo_dfrom, odoo_dto, False)

        return request.make_response('200 OK', [('Content-Type', 'text/plain')])

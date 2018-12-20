# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import json


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'

    @api.model
    def rm_get_reservation(self, Code=False):
        folio_res = self.env['hotel.folio'].search([('id', '=', Code)])
        json_response = dict()
        if len(folio_res) > 0:
            folio_lin = folio_res.room_lines
            json_response = {
                'Id': folio_res.id,
                'Arrival': folio_lin[0]['checkin'],
                'Departure': folio_lin[0]['checkout'],
                'Deposit': folio_res.amount_total,
                'Rooms': dict(),
                }
            for i, linea in enumerate(folio_lin):
                json_response['Rooms'][i] = {
                     'Id': linea.id,
                     'Adults': linea.adults,
                     'IsAvailable': 0,  # Need a function (Clean and no Checkin)
                     'Price': linea.price_total,
                     'RoomTypeId': linea.room_type_id.id,
                     'RoomTypeName': linea.room_type_id.name,
                     'RoomName': linea.room_id.name,
                     }
        json_response = json.dumps(json_response)

        return json_response

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <alex@aloxa.eu>
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
from openerp import models, fields, api
from openerp.exceptions import ValidationError
import re
import pytz


@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users
    # see bug 1086728
    return [(tz, tz) for tz in sorted(pytz.all_timezones,
                                      key=lambda tz: tz
                                      if not tz.startswith('Etc/') else '_')]


class HotelConfiguration(models.TransientModel):
    _name = 'hotel.config.settings'
    _inherit = 'res.config.settings'

    parity_pricelist_id = fields.Many2one('product.pricelist',
                                          'Product Pricelist')
    parity_restrictions_id = fields.Many2one('hotel.virtual.room.restriction',
                                             'Restrictions')
    default_arrival_hour = fields.Char('Default Arrival Hour (GMT)',
                                       help="HH:mm Format", default="14:00")
    default_departure_hour = fields.Char('Default Departure Hour (GMT)',
                                         help="HH:mm Format", default="12:00")
    tz_hotel = fields.Selection(_tz_get, string='Timezone',
                                default=lambda self: self._context.get('tz'),
                                help="The hotel's timezone, used to manage \
                                    date and time values in reservations \
                                    It is important to set a value for this \
                                    field.")

    @api.multi
    def set_parity_pricelist_id(self):
        pricelist_id = self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'parity_pricelist_id',
            self.parity_pricelist_id.id)
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        return pricelist_id

    @api.multi
    def set_parity_restrictions_id(self):
        restriction_id = self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'parity_restrictions_id',
            self.parity_restrictions_id.id)
        if restriction_id:
            restriction_id = int(restriction_id)
        return restriction_id

    @api.multi
    def set_tz_hotel(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'tz_hotel', self.tz_hotel)

    @api.multi
    def set_default_arrival_hour(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'default_arrival_hour',
            self.default_arrival_hour)

    @api.multi
    def set_default_departure_hour(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'default_departure_hour',
            self.default_departure_hour)

    @api.constrains('default_arrival_hour', 'default_departure_hour')
    def _check_hours(self):
        r = re.compile('[0-5][0-9]:[0-5][0-9]')
        if not r.match(self.default_arrival_hour):
            raise ValidationError("Invalid arrival hour (Format: HH:mm)")
            if not r.match(self.default_departure_hour):
                raise ValidationError("Invalid departure hour (Format: HH:mm)")

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018-2020  Alda Hotels <informatica@aldahotels.com>
#                             Jose Luis Algara <osotranquilo@gmail.com>
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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Inherit_hotel_reservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def urlcodefc(self, fecha):
        # Calculate de Secure Code to create url.
        compan = self.env.user.company_id
        d = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        delay = compan.fc_seeed_code * 100
        dtxt = float(d.strftime('%s.%%06d') % d.microsecond) + delay
        dtxt = repr(dtxt)[4:8]
        return dtxt

    @api.multi
    def fc_url_text(self, localizator, checkout):
        compan = self.env.user.company_id
        url = compan.fc_server + '/'
        url += str(compan.fc_server_id) + '/'
        url += localizator + '/'
        # url += '/' + self.urlcodefc(datetime.strftime(checkout, "%Y-%m-%d"))
        url += self.urlcodefc(checkout)
        return url

    @api.multi
    def _compute_fc_url(self):
        for res in self:
            res.fc_url = self.fc_url_text(res.localizator, res.checkout)

    fc_url = fields.Html('Fast Checkin URL',
                         compute='_compute_fc_url')

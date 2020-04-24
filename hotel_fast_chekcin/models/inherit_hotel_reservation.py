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
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Inherit_hotel_reservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def urlcodefc(self, fecha):
        # Calculate de Door Code... need a date in String format "%Y-%m-%d"
        compan = self.env.user.company_id
        if not compan.precode:
            compan.precode = ""
        if not compan.postcode:
            compan.postcode = ""
        d = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        delay = compan.seedcode * 100
        if compan.period == 7:
            dia_semana = datetime.weekday(d)  # Dias a restar para lunes
            d = d - timedelta(days=dia_semana)
        dtxt = float(d.strftime('%s.%%06d') % d.microsecond) + delay
        dtxt = compan.precode + repr(dtxt)[4:8] + compan.postcode
        return dtxt

    @api.multi
    def door_codes_text(self, localizator, checkout):
        compan = self.env.user.company_id
        url = compan.fc_server + '/' + localizator
        url += '/' + self.urlcodefc(datetime.strftime(checkout, "%Y-%m-%d"))
        return url

    @api.multi
    def _compute_fc_url(self):
        for res in self:
            res.fc_url = self.fc_url_text(res.localizator, res.checkout)

    fc_url = fields.Html('Fast Checkin URL',
                         compute='_compute_fc_url')

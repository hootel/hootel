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
from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Inherit_hotel_reservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def doorcode4(self, fecha):
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
    def door_codes_text(self, date_1, date_2):
        compan = self.env.user.company_id
        entrada = datetime.strptime(date_1[:10], DEFAULT_SERVER_DATE_FORMAT)
        salida = datetime.strptime(date_2[:10], DEFAULT_SERVER_DATE_FORMAT)
        codes = 'No data'
        if compan.period == 7:
            if datetime.weekday(entrada) == 0:
                entrada = entrada + timedelta(days=1)
            if datetime.weekday(salida) == 0:
                salida = salida - timedelta(days=1)
            codes = (_('Entry code: ') +
                     '<strong><span style="font-size: 1.4em;">' +
                     self.doorcode4(datetime.strftime(entrada, "%Y-%m-%d")) +
                     '</span></strong>')
            while entrada <= salida:
                if datetime.weekday(entrada) == 0:
                    codes += ("<br>" +
                              _('It will change on monday ') +
                              datetime.strftime(entrada, "%d-%m-%Y") +
                              _(' to:') +
                              ' <strong><span style="font-size: 1.4em;">' +
                              self.doorcode4(datetime.strftime(
                                  entrada, "%Y-%m-%d")) +
                              '</span></strong>')
                entrada = entrada + timedelta(days=1)
        else:
            codes = (_('Entry code: ') +
                     '<strong><span style="font-size: 1.4em;">' +
                     self.doorcode4(datetime.strftime(entrada, "%Y-%m-%d")) +
                     '</span></strong>')
            entrada = entrada + timedelta(days=1)
            while entrada < salida:
                codes += ("<br>" +
                          _('It will change on ') +
                          datetime.strftime(entrada, "%d-%m-%Y") +
                          _(' to:') +
                          ' <strong><span style="font-size: 1.4em;">' +
                          self.doorcode4(datetime.strftime(
                              entrada, "%Y-%m-%d")) +
                          '</span></strong>')
                entrada = entrada + timedelta(days=1)
        return codes

    @api.multi
    def _compute_door_codes(self):
        for res in self:
            res.door_codes = self.door_codes_text(res.checkin,
                                                  res.checkout)

    door_codes = fields.Html('Entry Codes',
                             compute='_compute_door_codes')
    box_number = fields.Integer('Box number')
    box_code = fields.Char('Box code')

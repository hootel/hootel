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
from odoo.exceptions import ValidationError


class Inherit_res_company(models.Model):
    @api.constrains('seedcode')
    def _check_seedcode(self):
        for compan in self:
            if compan.seedcode > 9999:
                raise ValidationError(_('The seed for the code must be a \
                                        maximum of 4 digits. Be between 0 \
                                        and 9999'))

    _inherit = 'res.company'

    precode = fields.Char('Characters before the door code', default='')
    postcode = fields.Char('Characters after the code', default='')
    period = fields.Selection([(7, 'Change Monday'), (1, 'Change Diary')],
                              string='Period of code change',
                              default=7,
                              required=True)
    seedcode = fields.Integer('4 digit Seed Code', default=0)

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
from openerp import models, fields


class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    fc_server = fields.Char('Fast Checkin Server', default='https://...')
    fc_server_id = fields.Integer('Server ID', default=0)
    fc_seeed_code = fields.Integer('2 digit Seed Code', default=99)
    fc_credit_journal = fields.Many2one('account.journal',
                                        string='Payment credit card journal',
                                        help='Credit card payment journal.',
                                        default=0)
    fc_cash_journal = fields.Many2one('account.journal',
                                      string='Payment cash journal',
                                      help='Cash payment journal.',
                                      default=0)

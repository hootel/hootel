# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------
from openerp import models, fields, api, _


class ResCompany(models.Model):

    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours',
                                      help="Provide the min hours value for \
                                        check in, checkout days, whatever \
                                        the hours will be provided here based \
                                        on that extra days will be \
                                        calculated.")
    default_cancel_policy_days = fields.Integer('Cancelation Days')
    default_cancel_policy_percent = fields.Integer('Percent to pay')

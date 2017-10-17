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

class HotelDashboard(models.Model):
    _name = "hotel.dashboard"

    def _get_count(self):
        quotations_count = self.env['sale.order'].search(
            [('sate', '=', 'draft')])
        orders_count = self.env['sale.order'].search(
            [('sate', '=', 'sales_order')])
        orders_done_count = self.env['sale.order'].search(
            [('sate', '=', 'done')])

        self.orders_count = len(orders_count)
        self.quotations_count = len(quotations_count)
        self.orders_done_count = len(orders_done_count)

    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name")
    reservations_count = fields.Integer(compute = '_get_count')
    folios_count = fields.Integer(compute= '_get_count')
    next_arrivals_count = fields.Integer(compute= '_get_count')

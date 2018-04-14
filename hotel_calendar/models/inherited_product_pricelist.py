# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def update_price(self, virtual_room_id, date, price):
        vroom = self.env['hotel.virtual.room'].browse(virtual_room_id)
        pritem_obj = self.env['product.pricelist.item']
        for record in self:
            plitem = pritem_obj.search([
                ('pricelist_id', '=', record.id),
                ('product_tmpl_id', '=', vroom.product_id.product_tmpl_id.id),
                ('date_start', '=', date),
                ('date_end', '=', date),
                ('applied_on', '=', '1_product'),
                ('compute_price', '=', 'fixed')
            ])
            if plitem:
                plitem.fixed_price = price
            else:
                pritem_obj.create({
                    'pricelist_id': record.id,
                    'product_tmpl_id': vroom.product_id.product_tmpl_id.id,
                    'date_start': date,
                    'date_end': date,
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'fixed_price': price
                })

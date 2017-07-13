# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
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
import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.model
    def create(self, vals):
        pricelist_id = vals.get('pricelist_id')
        product_tmpl_id = vals.get('product_tmpl_id')
        date_start = vals.get('date_start')
        vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)], limit=1)
        if pricelist_id and vroom:
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)

            self.env['bus.hotel.calendar'].send_pricelist_notification(
                pricelist_id,
                date_start,
                vroom.id,
                prod.price)
        return super(ProductPricelistItem, self).create(vals)

    @api.multi
    def write(self, vals):
        ret_vals = super(ProductPricelistItem, self).write(vals)
        if vals.get('fixed_price'):
            for record in self:
                pricelist_id = vals.get('pricelist_id') or record.pricelist_id.id
                date_start = vals.get('date_start') or record.date_start
                product_tmpl_id = vals.get('product_tmpl_id') or record.product_tmpl_id.id
                fixed_price = vals.get('fixed_price') or record.fixed_price
                vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)], limit=1)

                if vroom and date_start:
                    prod = vroom.product_id.with_context(
                        quantity=1,
                        date=date_start,
                        pricelist=pricelist_id)

                    self.env['bus.hotel.calendar'].send_pricelist_notification(
                        pricelist_id,
                        date_start,
                        vroom.id,
                        prod.price)
        return ret_vals

    @api.multi
    def unlink(self):
        pricelist_id = record.pricelist_id
        date_start = record.date_start
        vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', record.product_tmpl_id.id)], limit=1)
        res = super(HotelReservation, self).unlink()
        for record in self:
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)

            self.env['bus.hotel.calendar'].send_pricelist_notification(
                pricelist_id,
                date_start,
                vroom.id,
                prod.price)
        return res

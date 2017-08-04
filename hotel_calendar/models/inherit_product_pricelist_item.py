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
        res = super(ProductPricelistItem, self).create(vals)
        pricelist_parity_id = int(self.env['ir.property'].search([('name', '=', 'property_product_pricelist')], limit=1).value_reference.split(',')[1])
        pricelist_id = res.pricelist_id.id
        product_tmpl_id = res.product_tmpl_id.id
        date_start = res.date_start
        vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)], limit=1)
        if pricelist_id == pricelist_parity_id and vroom:
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)
            prod_price = prod.price

            self.env['bus.hotel.calendar'].send_pricelist_notification(
                pricelist_id,
                date_start,
                vroom.id,
                prod_price)

            vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
            vroom_pr_cached_id = vroom_pr_cached_obj.search([
                ('virtual_room_id', '=', vroom.id),
                ('date', '=', date_start),
            ], limit=1)
            if vroom_pr_cached_id:
                vroom_pr_cached_id.write({'price': prod_price})
            else:
                vroom_pr_cached_obj.create({
                    'virtual_room_id': vroom.id,
                    'date': date_start,
                    'price': prod_price,
                })
        return res

    @api.multi
    def write(self, vals):
        pricelist_parity_id = int(self.env['ir.property'].search([('name', '=', 'property_product_pricelist')], limit=1).value_reference.split(',')[1])
        ret_vals = super(ProductPricelistItem, self).write(vals)
        if vals.get('fixed_price'):
            for record in self:
                pricelist_id = vals.get('pricelist_id') or record.pricelist_id.id
                if not pricelist_id == pricelist_parity_id:
                    continue
                date_start = vals.get('date_start') or record.date_start
                product_tmpl_id = vals.get('product_tmpl_id') or record.product_tmpl_id.id
                fixed_price = vals.get('fixed_price') or record.fixed_price
                vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', product_tmpl_id)], limit=1)

                if vroom and date_start:
                    prod = vroom.product_id.with_context(
                        quantity=1,
                        date=date_start,
                        pricelist=pricelist_id)
                    prod_price = prod.price

                    self.env['bus.hotel.calendar'].send_pricelist_notification(
                        pricelist_id,
                        date_start,
                        vroom.id,
                        prod_price)

                    vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
                    vroom_pr_cached_id = vroom_pr_cached_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', date_start),
                    ], limit=1)
                    if vroom_pr_cached_id:
                        vroom_pr_cached_id.write({'price': prod_price})
        return ret_vals

    @api.multi
    def unlink(self):
        pricelist_parity_id = int(self.env['ir.property'].search([('name', '=', 'property_product_pricelist')], limit=1).value_reference.split(',')[1])
        unlink_vals = {}
        for record in self:
            if not record.pricelist_id == pricelist_parity_id:
                continue
            unlink_vals.update({
                'pricelist_id': record.pricelist_id,
                'date': record.date_start,
                'product_tmpl_id': record.product_tmpl_id.id
            })
        res = super(ProductPricelistItem, self).unlink()
        for vals in unlink_vals:
            pricelist_id = vals.pricelist_id
            date_start = vals.date_start
            vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', vals.product_tmpl_id.id)], limit=1)
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)

            self.env['bus.hotel.calendar'].send_pricelist_notification(
                pricelist_id,
                date_start,
                vroom.id,
                prod.price)

            vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
            vroom_pr_cached_id = vroom_pr_cached_obj.search([
                ('virtual_room_id', '=', vroom.id),
                ('date', '=', date_start),
            ], limit=1)
            if vroom_pr_cached_id:
                vroom_pr_cached_id.unlink()
        return res

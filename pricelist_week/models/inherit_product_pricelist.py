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
from itertools import chain
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
import time


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        results = super(ProductPricelist, self)._price_rule_get_multi(cr, uid, pricelist, products_by_qty_by_partner, context=context)
        if not any(results):
            return results

        date = context.get('date') and context['date'][0:10] or time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_dt = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
        products = map(lambda x: x[0], products_by_qty_by_partner)

        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        cr.execute(
            'SELECT i.id '
            'FROM product_pricelist_item AS i '
            'LEFT JOIN product_category AS c '
            'ON i.categ_id = c.id '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s))'
            'AND (product_id IS NULL OR product_id = any(%s))'
            'AND (categ_id IS NULL OR categ_id = any(%s)) '
            'AND (pricelist_id = %s) '
            'AND ((i.date_start IS NULL OR i.date_start<=%s) AND (i.date_end IS NULL OR i.date_end>=%s))'
            'ORDER BY applied_on, min_quantity desc, c.parent_left desc',
            (prod_tmpl_ids, prod_ids, categ_ids, pricelist.id, date, date))

        item_ids = [x[0] for x in cr.fetchall()]
        items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)
        for product, qty, partner in products_by_qty_by_partner:
            # if Public user try to access standard price from website sale, need to call _price_get.
            price = self.pool['product.template']._price_get(cr, uid, [product], 'list_price', context=context)[product.id]

            for rule in items:
                if (date_dt.weekday() == 0 and not rule.mo) or \
                        (date_dt.weekday() == 1 and not rule.tu) or \
                        (date_dt.weekday() == 2 and not rule.we) or \
                        (date_dt.weekday() == 3 and not rule.th) or \
                        (date_dt.weekday() == 4 and not rule.fr) or \
                        (date_dt.weekday() == 5 and not rule.sa) or \
                        (date_dt.weekday() == 6 and not rule.su):
                    results[product.id] = (price, False)

        return results

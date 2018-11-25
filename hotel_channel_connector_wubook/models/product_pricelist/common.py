# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductPricelistAdapter(Component):
    _name = 'channel.product.pricelist.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.product.pricelist'

    def get_pricing_plans(self):
        return super(ProductPricelistAdapter, self).get_pricing_plans()

    def create_plan(self, name):
        return super(ProductPricelistAdapter, self).create_plan(name)

    def delete_plan(self, external_id):
        return super(ProductPricelistAdapter, self).delete_plan(external_id)

    def rename_plan(self, external_id, new_name):
        return super(ProductPricelistAdapter, self).rename_plan(external_id, new_name)

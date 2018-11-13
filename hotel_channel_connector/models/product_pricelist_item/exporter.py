# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, api, _
_logger = logging.getLogger(__name__)

class ProductPricelistItemExporter(Component):
    _name = 'channel.product.pricelist.item.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.product.pricelist.item']
    _usage = 'product.pricelist.item.exporter'

    @api.model
    def push_pricelist(self):
        channel_product_pricelist_item_obj = self.env['channel.product.pricelist.item']
        channel_product_pricelist_obj = self.env['channel.product.pricelist']
        channel_room_type_obj = self.env['channel.hotel.room.type']
        channel_unpushed = channel_product_pricelist_item_obj.search([
            ('channel_pushed', '=', False),
            ('date_start', '>=', datetime.now().strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ], order="date_start ASC")
        if any(channel_unpushed):
            date_start = fields.Date.from_string(channel_unpushed[0].date_start)
            date_end = fields.Date.from_string(channel_unpushed[-1].date_start)
            days_diff = (date_start - date_end).days + 1

            prices = {}
            pricelist_ids = channel_product_pricelist_obj.search([
                ('external_id', '!=', False),
                ('active', '=', True)
            ])
            for pr in pricelist_ids:
                prices.update({pr.external_id: {}})
                unpushed_pl = channel_product_pricelist_item_obj.search(
                    [('channel_pushed', '=', False), ('pricelist_id', '=', pr.id)])
                product_tmpl_ids = unpushed_pl.mapped('product_tmpl_id')
                for pt_id in product_tmpl_ids:
                    channel_room_type = channel_room_type_obj.search([
                        ('product_id.product_tmpl_id', '=', pt_id.id)
                    ], limit=1)
                    if channel_room_type:
                        prices[pr.external_id].update({channel_room_type.external_id: []})
                        for i in range(0, days_diff):
                            prod = channel_room_type.product_id.with_context({
                                'quantity': 1,
                                'pricelist': pr.id,
                                'date': (date_start + timedelta(days=i)).
                                        strftime(DEFAULT_SERVER_DATE_FORMAT),
                                })
                            prices[pr.external_id][channel_room_type.external_id].append(prod.price)
            _logger.info("==[ODOO->CHANNEL]==== PRICELISTS ==")
            _logger.info(prices)
            for k_pk, v_pk in prices.items():
                if any(v_pk):
                    self.backend_adapter.update_plan_prices(k_pk, date_start.strftime(
                        DEFAULT_SERVER_DATE_FORMAT), v_pk)

            channel_unpushed.write({'channel_pushed': True})
        return True

# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ChannelProductPricelistItem(models.Model):
    _name = 'channel.product.pricelist.item'
    _inherit = 'channel.binding'
    _inherits = {'product.pricelist.item': 'odoo_id'}
    _description = 'Channel Product Pricelist Item'

    odoo_id = fields.Many2one(comodel_name='product.pricelist.item',
                              string='Hotel Product Pricelist Item',
                              required=True,
                              ondelete='cascade')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @job(default_channel='root.channel')
    @api.model
    def import_pricelist_values(self, backend, dfrom, dto, external_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='product.pricelist.item.importer')
            if not backend.pricelist_id:
                return importer.import_all_pricelist_values(
                    dfrom,
                    dto)
            return importer.import_pricelist_values(
                external_id,
                dfrom,
                dto)

    @job(default_channel='root.channel')
    @api.model
    def push_pricelist(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='product.pricelist.item.exporter')
            return exporter.push_pricelist()

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.product.pricelist.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

class BindingProductPricelistItemListener(Component):
    _name = 'binding.product.pricelist.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.pricelist.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('date_start', 'date_end', 'fixed_price', 'product_tmpl_id')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_bind_ids.write({'channel_pushed': False})

class ChannelBindingProductPricelistItemListener(Component):
    _name = 'channel.binding.product.pricelist.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('date_start', 'date_end', 'fixed_price', 'product_tmpl_id')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_pushed = False

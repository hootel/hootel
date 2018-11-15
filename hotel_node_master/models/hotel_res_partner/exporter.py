# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)


class NodeResPartnerExporter(Component):
    _name = 'node.res.partner.exporter'
    _inherit = 'node.exporter'
    _apply_on = ['node.res.partner']
    _usage = 'node.res.partner.exporter'

    @api.model
    def modify_res_partner(self, binding):
        return self.backend_adapter.modify_res_partner(
            binding.external_id,
            binding.name,
            binding.email,
            binding.is_company,
            binding.type
        )

    @api.model
    def delete_res_partner(self, binding):
        return self.backend_adapter.delete_res_partner(binding.external_id)

    @api.model
    def create_res_partner(self, binding):
        external_id = self.backend_adapter.create_res_partner(
            binding.name,
            binding.email,
            binding.is_company,
            binding.type
        )
        self.binder.bind(external_id, binding)

# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)


class NodeResGroupsExporter(Component):
    _name = 'node.res.groups.exporter'
    _inherit = 'node.exporter'
    _apply_on = ['node.res.groups']
    _usage = 'node.res.groups.exporter'

    @api.model
    def modify_res_groups(self, binding):
        return self.backend_adapter.modify_res_groups(
            binding.external_id,
            binding.name,
            # binding.user_ids
        )

    @api.model
    def delete_res_groups(self, binding):
        return self.backend_adapter.delete_res_groups(binding.external_id)

    @api.model
    def create_res_groups(self, binding):
        external_id = self.backend_adapter.create_res_groups(
            binding.name,
            # binding.user_ids
        )
        self.binder.bind(external_id, binding)

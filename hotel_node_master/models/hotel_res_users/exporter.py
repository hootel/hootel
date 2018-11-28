# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)


class NodeResUsersExporter(Component):
    _name = 'node.res.users.exporter'
    _inherit = 'node.exporter'
    _apply_on = ['node.res.users']
    _usage = 'node.res.users.exporter'

    @api.model
    def modify_res_users(self, binding):
        return self.backend_adapter.modify_res_users(
            binding.external_id,
            binding.login,
            binding.partner_id.external_id,
            # [r.external_id for r in binding.group_ids]
            # TODO Discuss where to do prepare commands for updating many2many fields
            [(6, False, [r.external_id for r in binding.group_ids])]

        )

    @api.model
    def delete_res_users(self, binding):
        return self.backend_adapter.delete_res_users(binding.external_id)

    @api.model
    def create_res_users(self, binding):
        external_id = self.backend_adapter.create_res_users(
            binding.login,
            binding.partner_id.external_id,
            # [r.external_id for r in binding.group_ids]
            # TODO Discuss where to do prepare commands for updating many2many fields
            [(6, False, [r.external_id for r in binding.group_ids])]
        )
        self.binder.bind(external_id, binding)

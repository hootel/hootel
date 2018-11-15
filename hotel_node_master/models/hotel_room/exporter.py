# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)


class NodeRoomExporter(Component):
    _name = 'node.room.exporter'
    _inherit = 'node.exporter'
    _apply_on = ['node.room']
    _usage = 'node.room.exporter'

    @api.model
    def modify_room(self, binding):
        return self.backend_adapter.modify_room(
            binding.external_id,
            binding.name,
            binding.capacity,
            # TODO Use .external_id is enough ?
            binding.room_type_id.external_id
        )

    @api.model
    def delete_room(self, binding):
        return self.backend_adapter.delete_room(binding.external_id)

    @api.model
    def create_room(self, binding):
        external_id = self.backend_adapter.create_room(
            binding.name,
            binding.capacity,
            # TODO Use .external_id is enough ?
            binding.room_type_id.external_id
        )
        self.binder.bind(external_id, binding)

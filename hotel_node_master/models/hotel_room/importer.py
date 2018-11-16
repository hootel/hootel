# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, follow_m2o_relations, m2o_to_external, external_to_m2o
from odoo import api, _
_logger = logging.getLogger(__name__)


class HotelRoomImporter(Component):
    _name = 'node.room.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.room']
    _usage = 'node.room.importer'

    @api.model
    def fetch_rooms(self):
        results = self.backend_adapter.fetch_rooms()
        room_mapper = self.component(usage='import.mapper',
                                     model_name='node.room')

        node_room_obj = self.env['node.room']
        for rec in results:
            map_record = room_mapper.map_record(rec)
            room = node_room_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', rec['id'])
            ])
            if room:
                room.write(map_record.values())
            else:
                room.with_context({'connector_no_export': True}).create(map_record.values(for_create=True))


class NodeRoomImportMapper(Component):
    _name = 'node.room.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.room'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
        ('capacity', 'capacity'),
        (external_to_m2o('room_type_id'), 'room_type_id')
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


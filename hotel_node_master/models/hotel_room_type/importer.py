# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import api, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeImporter(Component):
    _name = 'node.room.type.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.room.type']
    _usage = 'node.room.type.importer'

    @api.model
    def fetch_room_types(self):
        results = self.backend_adapter.fetch_room_types()
        room_type_mapper = self.component(usage='import.mapper',
                                          model_name='node.room.type')

        node_room_type_obj = self.env['node.room.type']
        for rec in results:
            map_record = room_type_mapper.map_record(rec)
            room_type = node_room_type_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', rec['id'])
            ])
            if room_type:
                room_type.with_context({'connector_no_export': True}).write(map_record.values())
            else:
                room_type.with_context({'connector_no_export': True}).create(map_record.values(for_create=True))

    @api.model
    def fetch_room_type_availability(self, checkin, checkout, room_type_id):
        return self.backend_adapter.fetch_room_type_availability(checkin, checkout, room_type_id)

    @api.model
    def fetch_room_type_price_unit(self, checkin, checkout, room_type_id):
        return self.backend_adapter.fetch_room_type_price_unit(checkin, checkout, room_type_id)

    @api.model
    def fetch_room_type_restrictions(self, checkin, checkout, room_type_id):
        return self.backend_adapter.fetch_room_type_restrictions(checkin, checkout, room_type_id)

    @api.model
    def fetch_room_type_planning(self, checkin, checkout, room_type_id):
        return self.backend_adapter.fetch_room_type_planning(checkin, checkout, room_type_id)


class NodeRoomTypeImportMapper(Component):
    _name = 'node.room.type.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.room.type'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
    ]
    # children = [('room_ids', 'room_ids', 'node.room')]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}



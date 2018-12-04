# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api


class HotelRoomTypeImporter(Component):
    _inherit = 'channel.hotel.room.type.importer'

    @api.model
    def get_rooms(self):
        count = 0
        try:
            results = self.backend_adapter.fetch_rooms()
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            channel_room_type_obj = self.env['channel.hotel.room.type']
            hotel_room_type_class_obj = self.env['hotel.room.type.class']
            room_mapper = self.component(usage='import.mapper',
                                         model_name='channel.hotel.room.type')
            for room in results:
                room_type_class = hotel_room_type_class_obj.search([
                    ('code_class', '=', str(room['rtype'])),
                ])
                room.update({
                    'class_id': room_type_class and room_type_class.id or False,
                })
                map_record = room_mapper.map_record(room)
                room_bind = channel_room_type_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', room['id']),
                ], limit=1)
                if room_bind:
                    room_bind.with_context({'connector_no_export':True}).write(map_record.values())
                else:
                    room_bind = channel_room_type_obj.with_context({
                        'connector_no_export':True}).create(
                            map_record.values(for_create=True))
                    self.binder.bind(room['id'], room_bind)
                count = count + 1
        return count


class HotelRoomTypeImportMapper(Component):
    _name = 'channel.hotel.room.type.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type'

    direct = [
        ('id', 'external_id'),
        ('shortname', 'channel_short_code'),
        ('occupancy', 'ota_capacity'),
        ('price', 'list_price'),
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def class_id(self, record):
        return {'class_id': record['class_id']}

# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, fields, _
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
_logger = logging.getLogger(__name__)

class HotelRoomTypeAvailabilityExporter(Component):
    _name = 'channel.hotel.room.type.availability.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.availability']
    _usage = 'hotel.room.type.availability.exporter'

    def push_availability(self):
        channel_room_type_avail_ids = self.env['channel.hotel.room.type.availability'].search([
            ('channel_pushed', '=', False),
            ('date', '>=', fields.Date.today())
        ])
        room_types = channel_room_type_avail_ids.mapped('room_type_id')
        avails = []
        for room_type in room_types:
            if any(room_type.channel_bind_ids):
                channel_room_type_avails = channel_room_type_avail_ids.filtered(
                    lambda x: x.room_type_id.id == room_type.id)
                days = []
                for channel_room_type_avail in channel_room_type_avails:
                    channel_room_type_avail.channel_pushed = True
                    cavail = channel_room_type_avail.avail
                    if channel_room_type_avail.channel_max_avail >= 0 and \
                            cavail > channel_room_type_avail.channel_max_avail:
                        cavail = channel_room_type_avail.channel_max_avail
                    date_dt = fields.Date.from_string(channel_room_type_avail.date)
                    days.append({
                        'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': cavail,
                        'no_ota': channel_room_type_avail.no_ota and 1 or 0,
                        # 'booked': room_type_avail.booked and 1 or 0,
                    })
                avails.append({'id': room_type.channel_bind_ids[0].channel_room_id, 'days': days})
        _logger.info("==[ODOO->CHANNEL]==== AVAILABILITY ==")
        _logger.info(avails)
        if any(avails):
            self.backend_adapter.update_availability(avails)

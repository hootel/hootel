# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _
from odoo.exceptions import ValidationError


class HotelRoomTypeDeleter(Component):
    _inherit = 'channel.hotel.room.type.deleter'

    @api.model
    def delete_room(self, binding):
        try:
            return self.backend_adapter.delete_room(binding.external_id)
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']) + ". " + _(str(err)))

# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class NodeRoom(models.Model):
    _name = 'node.room'
    _inherit = 'node.binding'
    _description = 'Node Hotel Room'

    name = fields.Char('Room Name', required=True)
    room_type_id = fields.Many2one('node.room.type', 'Hotel Room Type',
                                   required=True,
                                   ondelete='restrict')
    capacity = fields.Integer('Capacity')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)

    @api.multi
    def write(self, vals):
        for rec in self:
            if 'backend_id' in vals and vals['backend_id'] != rec.backend_id.id:
                msg = _("Changing a record between backends is not allowed. "
                        "Please create a new one in the corresponding backend.")
                _logger.warning(msg)
                raise UserError(msg)
        return super().write(vals)

    @job(default_channel='root.channel')
    @api.model
    def create_room(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.exporter')
            return exporter.create_room(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_room(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.exporter')
            return exporter.modify_room(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_room(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.exporter')
            return exporter.delete_room(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_rooms(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.importer')
            return importer.fetch_rooms()


class NodeRoomAdapter(Component):
    _name = 'node.room.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.room'

    def create_room(self, name, capacity, room_type_id):
        return super().create_room(name, capacity, room_type_id)

    def modify_room(self, room_id, name, capacity, room_type_id):
        return super().modify_room(room_id, name, capacity, room_type_id)

    def delete_room(self, room_id):
        return super().delete_room(room_id)

    def fetch_rooms(self):
        return super().fetch_rooms()


class NodeBindingRoomListener(Component):
    _name = 'node.binding.room.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.room']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_room()

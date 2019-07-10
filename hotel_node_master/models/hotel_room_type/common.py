# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class NodeRoomType(models.Model):
    _name = 'node.room.type'
    _inherit = 'node.binding'
    _description = 'Node Hotel Room Type'

    name = fields.Char(required=True, translate=True)
    room_ids = fields.One2many('node.room', 'room_type_id', 'Rooms')
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
    def create_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.create_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.modify_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_room_type(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.room.type.exporter')
            return exporter.delete_room_type(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_types(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_types()

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_type_availability(self, backend, checkin, checkout, room_type_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_type_availability(checkin, checkout, room_type_id)

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_type_price_unit(self, backend, checkin, checkout, room_type_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_type_price_unit(checkin, checkout, room_type_id)

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_type_restrictions(self, backend, checkin, checkout, room_type_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_type_restrictions(checkin, checkout, room_type_id)

    @job(default_channel='root.channel')
    @api.model
    def fetch_room_type_planning(self, backend, checkin, checkout, room_type_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.room.type.importer')
            return importer.fetch_room_type_planning(checkin, checkout, room_type_id)

class NodeRoomTypeAdapter(Component):
    _name = 'node.room.type.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.room.type'

    def create_room_type(self, name, room_ids):
        return super().create_room_type(name, room_ids)

    def modify_room_type(self, room_type_id, name, room_ids):
        return super().modify_room_type(room_type_id, name, room_ids)

    def delete_room_type(self, room_type_id):
        return super().delete_room_type(room_type_id)

    def fetch_room_types(self):
        return super().fetch_room_types()

    def fetch_room_type_availability(self, checkin, checkout, room_type_id):
        return super().fetch_room_type_availability(checkin, checkout, room_type_id)

    def fetch_room_type_price_unit(self, checkin, checkout, room_type_id):
        return super().fetch_room_type_price_unit(checkin, checkout, room_type_id)

    def fetch_room_type_restrictions(self, checkin, checkout, room_type_id):
        return super().fetch_room_type_restrictions(checkin, checkout, room_type_id)

    def fetch_room_type_planning(self, checkin, checkout, room_type_id):
        return super().fetch_room_type_planning(checkin, checkout, room_type_id)


class NodeBindingRoomTypeListener(Component):
    _name = 'node.binding.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_room_type()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_room_type()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_room_type()

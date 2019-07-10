# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class NodeResGroups(models.Model):
    _name = 'node.res.groups'
    _inherit = 'node.binding'
    _description = 'Node Hotel Groups'

    name = fields.Char(required=True)
    user_ids = fields.Many2many('node.res.users', 'node_res_groups_users_rel', 'gid', 'uid', string='Users')
    active = fields.Boolean(default=True)

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
    def create_res_groups(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.groups.exporter')
            return exporter.create_res_groups(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_res_groups(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.groups.exporter')
            return exporter.modify_res_groups(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_res_groups(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.groups.exporter')
            return exporter.delete_res_groups(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_res_groups(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.res.groups.importer')
            return importer.fetch_res_groups()


class NodeResGroupsAdapter(Component):
    _name = 'node.res.groups.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.res.groups'

    def create_res_groups(self, name, user_ids):
        return super().create_res_groups(name, user_ids)

    def modify_res_groups(self, group_id, name, user_ids):
        return super().modify_res_groups(group_id, name, user_ids)

    def delete_res_groups(self, group_id):
        return super().delete_res_groups(group_id)

    def fetch_res_groups(self):
        return super().fetch_res_groups()


class NodeBindingResGroupsListener(Component):
    _name = 'node.binding.res.groups.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.res.groups']

    # TODO If Groups are only readonly we do not need a base.connector.listener

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_res_groups()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_res_groups()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_res_groups()

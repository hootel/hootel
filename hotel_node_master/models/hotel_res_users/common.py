# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class NodeResUsers(models.Model):
    _name = 'node.res.users'
    _inherit = 'node.binding'
    _description = 'Node Hotel Users'

    master_user_id = fields.Many2one(comodel_name='master.res.users',
                                     string='Users',
                                     required=True,
                                     ondelete='cascade')
    login = fields.Char(related='master_user_id.login', readonly=True, help="Used to log into the system")

    partner_id = fields.Many2one('node.res.partner', required=True, ondelete='restrict',
                                 string='Related Partner', help='Partner-related data of the user')
    name = fields.Char(related='partner_id.name', readonly=True)
    email = fields.Char(related='partner_id.email', readonly=True)

    group_ids = fields.Many2many('node.res.groups', 'node_res_groups_users_rel', 'uid', 'gid', string='Groups')

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
    def create_res_users(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.users.exporter')
            return exporter.create_res_users(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_res_users(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.users.exporter')
            return exporter.modify_res_users(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_res_users(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.users.exporter')
            return exporter.delete_res_users(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_res_users(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.res.users.importer')
            return importer.fetch_res_users()


class NodeResUsersAdapter(Component):
    _name = 'node.res.users.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.res.users'

    def create_res_users(self, login, active, partner_id, group_ids):
        return super().create_res_users(login, active, partner_id, group_ids)

    def modify_res_users(self, user_id, login, active, partner_id, group_ids):
        return super().modify_res_users(user_id, login, active, partner_id, group_ids)

    def delete_res_users(self, user_id):
        return super().delete_res_users(user_id)

    def fetch_res_users(self):
        return super().fetch_res_users()


class NodeBindingResUsersListener(Component):
    _name = 'node.binding.res.users.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.res.users']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_res_users()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_res_users()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_res_users()


class MasterResUsers(models.Model):
    _name = 'master.res.users'
    _description = 'Centralized Users'

    partner_id = fields.Many2one('node.res.partner', required=True, ondelete='restrict',
                                 string='Related Partner', help='Partner-related data of the user')
    name = fields.Char(related='partner_id.name', readonly=True)
    login = fields.Char(required=True, help="Used to log into the system")
    node_binding_ids = fields.One2many('node.res.users', 'master_user_id',
                                       'Node Users binded to this one')

    _sql_constraints = [
        ('login_id_uniq', 'unique(login)',
         'You can not have two users with the same login !'),
    ]

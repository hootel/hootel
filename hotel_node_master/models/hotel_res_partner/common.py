# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
_logger = logging.getLogger(__name__)


class NodeResPartner(models.Model):
    _name = 'node.res.partner'
    _inherit = 'node.binding'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'Node Hotel Partners'

    odoo_id = fields.Many2one(comodel_name='res.partner',
                              string='Partners',
                              required=True,
                              ondelete='cascade')
    node_user_ids = fields.One2many('node.res.users', 'partner_id', string='Node Users')

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
    def create_res_partner(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.partner.exporter')
            return exporter.create_res_partner(self)

    @job(default_channel='root.channel')
    @api.model
    def modify_res_partner(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.partner.exporter')
            return exporter.modify_res_partner(self)

    @job(default_channel='root.channel')
    @api.model
    def delete_res_partner(self):
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='node.res.partner.exporter')
            return exporter.delete_res_partner(self)

    @job(default_channel='root.channel')
    @api.model
    def fetch_res_partners(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='node.res.partner.importer')
            return importer.fetch_res_partners()


class NodeResPartnerAdapter(Component):
    _name = 'node.res.partner.adapter'
    _inherit = 'hotel.node.adapter'
    _apply_on = 'node.res.partner'

    def create_res_partner(self, name, email, is_company, type):
        return super().create_res_partner(name, email, is_company, type)

    def modify_res_partner(self, partner_id, name, email, is_company, type):
        return super().modify_res_partner(partner_id, name, email, is_company, type)

    def delete_res_partner(self, partner_id):
        return super().delete_res_partner(partner_id)

    def fetch_res_partners(self):
        return super().fetch_res_partners()


class NodeBindingResPartnerListener(Component):
    _name = 'node.binding.res.partner.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['node.res.partner']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_res_partner()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_res_partner()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.modify_res_partner()


class ResPartner(models.Model):

    _inherit = 'res.partner'

    node_binding_ids = fields.One2many('node.res.partner', 'odoo_id',
                                       'Node Partners binded to this one')

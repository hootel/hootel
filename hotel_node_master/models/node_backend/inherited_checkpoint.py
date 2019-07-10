# Copyright 2018 Pablo Q. Barriuso
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, _


class ConnectorCheckpoint(models.Model):
    _inherit = 'connector.checkpoint'

    @api.model
    def create_from_name(self, model_name, record_id,
                         backend_model_name, backend_id):
        record = super().create_from_name(model_name, record_id,
                                          backend_model_name, backend_id)
        msg = _("User '%s' with external ID [%s] imported from node https://%s needs a review "
                "because it is using an existing login: [%s]") % (record.name, record.record.external_id,
                                                                  record.backend_id.address, record.record.login)
        record.record.active = False
        record.message_post(body=msg, subtype='mail.mt_comment')

        return record

    @api.multi
    def reviewed(self):
        self.record.active = True
        return self.write({'state': 'reviewed'})

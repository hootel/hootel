# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import api, _
_logger = logging.getLogger(__name__)


class HotelResPartnerImporter(Component):
    _name = 'node.res.partner.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.res.partner']
    _usage = 'node.res.partner.importer'

    @api.model
    def fetch_res_partners(self):
        results = self.backend_adapter.fetch_res_partners()
        res_partner_mapper = self.component(usage='import.mapper',
                                          model_name='node.res.partner')

        node_res_partner_obj = self.env['node.res.partner']
        for rec in results:
            map_record = res_partner_mapper.map_record(rec)
            res_partner = node_res_partner_obj.search([('external_id', '=', rec['id'])],
                                                  limit=1)
            if res_partner:
                res_partner.write(map_record.values())
            else:
                res_partner.with_context({'connector_no_export': True}).create(map_record.values(for_create=True))


class NodeResPartnerImportMapper(Component):
    _name = 'node.res.partner.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.res.partner'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
        ('email', 'email'),
        ('is_company', 'is_company'),
        ('type', 'type'),
    ]


    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}



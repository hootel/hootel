# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import api, _

_logger = logging.getLogger(__name__)


class HotelResGroupsImporter(Component):
    _name = 'node.res.groups.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.res.groups']
    _usage = 'node.res.groups.importer'

    @api.model
    def fetch_res_groups(self):
        results = self.backend_adapter.fetch_res_groups()
        res_groups_mapper = self.component(usage='import.mapper',
                                           model_name='node.res.groups')

        node_res_groups_obj = self.env['node.res.groups']
        for rec in results:
            map_record = res_groups_mapper.map_record(rec)
            node_res_groups = node_res_groups_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', rec['id'])
            ])
            if node_res_groups:
                node_res_groups.with_context(
                    {'connector_no_export': True}).write(map_record.values())
            else:
                node_res_groups.with_context(
                    {'connector_no_export': True}).create(map_record.values(for_create=True))


class NodeResGroupsImportMapper(Component):
    _name = 'node.res.groups.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.res.groups'

    direct = [
        ('id', 'external_id'),
        ('full_name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


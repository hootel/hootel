# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, external_to_m2o
from odoo import api, _

_logger = logging.getLogger(__name__)


class HotelResUsersImporter(Component):
    _name = 'node.res.users.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.res.users']
    _usage = 'node.res.users.importer'

    @api.model
    def fetch_res_users(self):
        results = self.backend_adapter.fetch_res_users()
        res_users_mapper = self.component(usage='import.mapper',
                                          model_name='node.res.users')

        # TODO first import partners and groups and then users, so they keep linked
        node_res_users_obj = self.env['node.res.users']
        for rec in results:
            map_record = res_users_mapper.map_record(rec)
            node_res_users = node_res_users_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', rec['id'])
            ])
            # TODO Merge users among nodes by login / email
            if node_res_users:
                node_res_users.with_context(
                    {'connector_no_export': True}).write(map_record.values())
            else:
                node_res_users.with_context(
                    {'connector_no_export': True}).create(map_record.values(for_create=True))

            # TODO mark record with duplicate key value in constraint "node_res_users_login_id_uniq" as checkpoint


class NodeResUsersImportMapper(Component):
    _name = 'node.res.users.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.res.users'

    direct = [
        ('id', 'external_id'),
        ('login', 'login'),
        (external_to_m2o('partner_id'), 'partner_id')
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

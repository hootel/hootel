# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from odoo import models, api, fields
from ...components.backend_adapter import NodeLogin, NodeServer


class NodeBackend(models.Model):
    _name = 'node.backend'
    _description = 'Hotel Node Backend'
    _inherit = 'connector.backend'

    name = fields.Char('Name')
    address = fields.Char('Host', required=True,
                          help='Full URL to the host.')
    db = fields.Char('Database Name',
                     help='Odoo database name.')
    user = fields.Char('Username',
                       help='Odoo administration user.')
    passwd = fields.Char('Password',
                         help='Odoo password.')
    port = fields.Integer(string='TCP Port', default=443,
                          help='Specify the TCP port for the XML-RPC protocol.')
    protocol = fields.Selection([('jsonrpc', 'jsonrpc'), ('jsonrpc+ssl', 'jsonrpc+ssl')],
                                'Protocol', required=True, default='jsonrpc+ssl')
    odoo_version = fields.Char()

    room_type_ids = fields.One2many('node.room.type', 'backend_id', 'Room Types')
    room_ids = fields.One2many('node.room', 'backend_id', 'Rooms')
    group_ids = fields.One2many('node.res.groups', 'backend_id', 'Access Groups')
    user_ids = fields.One2many('node.res.users', 'backend_id', 'Users with access to this hotel',
                               domain=['|', ('active', '=', True), ('active', '=', False)])

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        node_login = NodeLogin(
            self.address,
            self.protocol,
            self.port,
            self.db,
            self.user,
            self.passwd)
        with NodeServer(node_login) as node_api:
            _super = super(NodeBackend, self)
            with _super.work_on(model_name, node_api=node_api, **kwargs) as work:
                yield work

    @api.multi
    def test_connection(self):
        pass

    @api.multi
    def import_room_types(self):
        node_room_type_obj = self.env['node.room.type']
        for backend in self:
            node_room_type_obj.fetch_room_types(backend)

    @api.multi
    def import_rooms(self):
        node_room_obj = self.env['node.room']
        for backend in self:
            node_room_obj.fetch_rooms(backend)

    @api.multi
    def import_partners(self):
        node_res_partner_obj = self.env['node.res.partner']
        for backend in self:
            node_res_partner_obj.fetch_res_partners(backend)

    @api.multi
    def import_groups(self):
        node_res_groups_obj = self.env['node.res.groups']
        for backend in self:
            node_res_groups_obj.fetch_res_groups(backend)

    @api.multi
    def import_users(self):
        node_res_users_obj = self.env['node.res.users']
        for backend in self:
            node_res_users_obj.fetch_res_users(backend)

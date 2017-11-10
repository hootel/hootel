# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from odoo.release import version_info
import xmlrpclib

class NodeSlaveInstaller(models.TransientModel):
    NODE_MASTER_ADDRESS_KEY = "Node.Master.Address"
    NODE_MASTER_DB_KEY = "Node.Master.DataBase"
    NODE_MASTER_USER_KEY = "Node.Master.User"
    NODE_MASTER_UID_KEY = "Node.Master.UID"
    NODE_MASTER_PASSWD_KEY = "Node.Master.Password"
    GROUPS = ['base.group_system']

    _name = 'hotel.node.slave.installer'
    _inherit = 'res.config.installer'

    node_master_address = fields.Char('Node Master Address', required=True, default="https://")
    node_master_database = fields.Char('Node Master DataBase', required=True)
    node_master_user = fields.Char('Node Master User', required=True)
    node_master_passwd = fields.Char('Node Master Password', required=True)

    @api.multi
    def execute(self):
        super(NodeSlaveInstaller, self).execute()
        self.execute_simple()
        self._check_connection():
        return True

    @api.multi
    def execute_simple(self):
        icp = self.env['ir.config_parameter'].sudo()
        for rec in self:
            icp.set_param(NODE_MASTER_ADDRESS_KEY, rec.node_master_address, groups=self.GROUPS)
            icp.set_param(NODE_MASTER_DB_KEY, rec.node_master_database, groups=self.GROUPS)
            icp.set_param(NODE_MASTER_USER_KEY, rec.node_master_user, groups=self.GROUPS)
            icp.set_param(NODE_MASTER_PASSWD_KEY, rec.node_master_passwd, groups=self.GROUPS)
        return True

    @api.model
    def _check_connection(self):
        master_address = self.env['ir.config_parameter'].get_param(NODE_MASTER_ADDRESS_KEY)
        master_db = self.env['ir.config_parameter'].get_param(NODE_MASTER_DB_KEY)
        master_user = self.env['ir.config_parameter'].get_param(NODE_MASTER_USER_KEY)
        master_passwd = self.env['ir.config_parameter'].get_param(NODE_MASTER_PASSWD_KEY)

        common = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % master_address)
        if not common:
            raise ValidationError("ERROR: Can't connect with master node!")
        master_ver_info = common.version()['server_version_info']
        if not master_ver_info == version_info:
            raise ValidationError("ERROR: Master node uses a different Odoo version (%d.%d)" % (master_ver_info[0], master_ver_info[1])))
        uid = common.authenticate(master_db, master_user, master_passwd, {})
        self.env['ir.config_parameter'].sudo().set_param(NODE_MASTER_UID_KEY, uid, groups=self.GROUPS)
        return uid

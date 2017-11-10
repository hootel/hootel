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
from odoo_rpc_client import Client
from odoo import api, SUPERUSER_ID


# WUBOOK
class HotelNodeSlave(models.TransientModel):
    COMMON = None
    MODELS = None
    UID = None
    MASTER_ADDRESS = None
    MASTER_DATABASE = None
    MASTER_USER = None
    MASTER_PASSWD = None

    _name = 'HotelNodeSlave'

    def login(self):
        self.MASTER_ADDRESS = self.env['ir.config_parameter'].get_param(NODE_MASTER_ADDRESS_KEY)
        self.MASTER_DATABASE = self.env['ir.config_parameter'].get_param(NODE_MASTER_DB_KEY)
        self.MASTER_USER = self.env['ir.config_parameter'].get_param(NODE_MASTER_USER_KEY)
        self.MASTER_PASSWD = self.env['ir.config_parameter'].get_param(NODE_MASTER_PASSWD_KEY)

        self.COMMON = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % self.MASTER_ADDRESS)
        if not self.COMMON:
            return False
        self.UID = self.COMMON.authenticate(self.MASTER_DATABASE, self.MASTER_USER, self.MASTER_PASSWD, {})
        if not self.UID:
            return False
        self.MODELS = xmlrpclib.ServerProxy('%s/xmlrpc/2/object' % self.MASTER_ADDRESS)
        return True


    @api.model
    def create_record(self, model, records):
        for rec in records:
            if hasattr(rec, 'id'):
                del rec.id
        return models.execute_kw(self.MASTER_DATABASE, self.UID, self.MASTER_PASSWD, model, 'create', records)

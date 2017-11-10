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
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        partner_id = super(ResPartner, self).create(vals)

        icp =  self.env['ir.config_parameter'].sudo()
        master_address = icp.get_param(NODE_MASTER_ADDRESS_KEY)
        master_db = icp.get_param(NODE_MASTER_DB_KEY)
        master_uid = icp.get_param(NODE_MASTER_UID_KEY)
        master_passwd = icp.get_param(NODE_MASTER_PASSWD_KEY)
        master_models = xmlrpclib.ServerProxy('%s/xmlrpc/2/object' % master_address)
        master_user_id = master_models.execute_kw(master_db, master_uid, master_passwd,
            'res.users', 'read', [[master_uid]], {'limit': 1})

        master_models.execute_kw(db, uid, password, 'res.partner', 'create', [{
            'name': partner_id.name,
            'city': partner_id.city,
            'company_type': 'person',
            'parent_id': master_user_id.parent_id[0]
            'address_type': 'contact',
            'city': partner_id.city,
            'street': partner_id.street,
            'street2': partner_id.street2,
            'city': partner_id.city,
            'state_id': partner_id.state_id.id,
            'zip': partner_id.zip,
            'country_id': partner_id.country_id.id,
            'email': partner_id.email
        }])

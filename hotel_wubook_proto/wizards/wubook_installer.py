# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
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
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class WuBookInstaller(models.TransientModel):
    _name = 'wubook.installer'
    _inherit = 'res.config.installer'

    wubook_user = fields.Char('User', required=True)
    wubook_passwd = fields.Char('Password', required=True)
    wubook_lcode = fields.Char('LCode', required=True)
    wubook_server = fields.Char(string='Server',
                                default='https://wubook.net/xrws/',
                                required=True)
    wubook_pkey = fields.Char('PKey', required=True)

    @api.cr_uid_ids_context
    def execute(self, cr, uid, ids, context=None):
        records = self.browse(cr, uid, ids, context=context)
        records.execute_simple()
        return super(WuBookInstaller, self).execute(cr, uid, ids,
                                                    context=context)

    @api.multi
    def execute_simple(self):
        for rec in self:
            self.env['ir.values'].set_default('wubook.config.settings', 'wubook_user', rec.wubook_user)
            self.env['ir.values'].set_default('wubook.config.settings', 'wubook_passwd', rec.wubook_passwd)
            self.env['ir.values'].set_default('wubook.config.settings', 'wubook_lcode', rec.wubook_lcode)
            self.env['ir.values'].set_default('wubook.config.settings', 'wubook_server', rec.wubook_server)
            self.env['ir.values'].set_default('wubook.config.settings', 'wubook_pkey', rec.wubook_pkey)
        wres = self.env['wubook'].initialize()
        if not wres:
            raise ValidationError("Can't finish installation!")

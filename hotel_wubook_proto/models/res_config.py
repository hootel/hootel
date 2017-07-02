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
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID


class wubook_configuration(osv.osv_memory):
    _name = 'wubook.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'wubook_user': fields.char('WuBook User'),
        'wubook_passwd': fields.char('WuBook Password'),
        'wubook_lcode': fields.char('WuBook lcode'),
        'wubook_server': fields.char('WuBook Server'),
        'wubook_pkey': fields.char('WuBook PKey'),
    }

    _defaults = {
        'wubook_server': 'https://wubook.net/xrws/',
    }

    def set_wubook_user(self, cr, uid, ids, context=None):
        user = self.browse(cr, uid, ids, context=context).wubook_user
        res = self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'wubook.config.settings', 'wubook_user', user)
        return res

    def set_wubook_passwd(self, cr, uid, ids, context=None):
        passwd = self.browse(cr, uid, ids, context=context).wubook_passwd
        res = self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'wubook.config.settings', 'wubook_passwd', passwd)
        return res

    def set_wubook_lcode(self, cr, uid, ids, context=None):
        lcode = self.browse(cr, uid, ids, context=context).wubook_lcode
        res = self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'wubook.config.settings', 'wubook_lcode', lcode)
        return res

    def set_wubook_server(self, cr, uid, ids, context=None):
        server = self.browse(cr, uid, ids, context=context).wubook_server
        res = self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'wubook.config.settings', 'wubook_server', server)
        return res

    def set_wubook_pkey(self, cr, uid, ids, context=None):
        pkey = self.browse(cr, uid, ids, context=context).wubook_pkey
        res = self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'wubook.config.settings', 'wubook_pkey', pkey)
        return res

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
from openerp import models, fields, api


class WubookConfiguration(models.TransientModel):
    _name = 'wubook.config.settings'
    _inherit = 'res.config.settings'

    wubook_user = fields.Char('WuBook User')
    wubook_passwd = fields.Char('WuBook Password')
    wubook_lcode = fields.Char('WuBook lcode')
    wubook_server = fields.Char('WuBook Server', default='https://wubook.net/xrws/')
    wubook_pkey = fields.Char('WuBook PKey')


    @api.multi
    def set_wubook_user(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_user', self.wubook_user)

    @api.multi
    def set_wubook_passwd(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_passwd', self.wubook_passwd)

    @api.multi
    def set_wubook_lcode(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_lcode', self.wubook_lcode)

    @api.multi
    def set_wubook_server(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_server', self.wubook_server)

    @api.multi
    def set_wubook_pkey(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_pkey', self.wubook_pkey)

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


class hotel_virtual_room(models.Model):
    _inherit = 'hotel.virtual.room'

    wscode = fields.Char("WuBook Short Code")
    wrid = fields.Char("WuBook Room ID", readonly=True)

    @api.multi
    def create(self, vals):
        if self._context.get('wubook_action', True):
            vals = self.env['wubook'].create_room(vals)
        return super(hotel_virtual_room, self).create(vals)

    @api.multi
    def write(self, vals):
        ret_vals = super(hotel_virtual_room, self).write(vals)
        if self._context.get('wubook_action', True):
            for record in self:
                self.env['wubook'].modify_room(record.id)
        return ret_vals

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True):
            for record in self:
                self.env['wubook'].delete_room(record.id)
        return super(hotel_virtual_room, self).unlink()

    @api.multi
    def import_rooms(self):
        wubook = self.env['wubook']
        wubook.import_rooms()
        return True
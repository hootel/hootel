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
from openerp.exceptions import ValidationError


class VirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    @api.model
    def _default_wmax_avail(self):
        if self.virtual_room_id:
            return self.virtual_room_id.max_real_rooms
        return -1

    wmax_avail = fields.Integer("Max. Wubook Avail",
                                default=_default_wmax_avail)
    wpushed = fields.Boolean("WuBook Pushed", readonly=True, default=False)

    @api.constrains('wmax_avail')
    def _check_wmax_avail(self):
        if self.wmax_avail > self.virtual_room_id.total_rooms_count:
            raise ValidationError("max avail for wubook can't be high \
                than toal rooms \
                    count: %d" % self.virtual_room_id.total_rooms_count)

    @api.onchange('virtual_room_id')
    def onchange_virtual_room_id(self):
        if self.virtual_room_id:
            self.wmax_avail = self.virtual_room_id.max_real_rooms

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vals.update({'wpushed': False})
        return super(VirtualRoomAvailability, self).write(vals)

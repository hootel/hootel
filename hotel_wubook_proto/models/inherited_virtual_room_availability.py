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

    wmax_avail = filed.Integer("Max. Wubook Avail", default=-1)
    wpushed = fields.Boolean("WuBook Pushed", readonly=True, default=False)

    @api.constrains('wmax_avail')
    def _check_wmax_avail(self):
        vroom_obj = self.env['hotel.virtual.room']
        cavail = len(vroom_obj.check_availability_virtual_room(
            self.date,
            self.date,
            virtual_room_id=self.virtual_room_id.id))
        max_avail = min(cavail,
                        self.virtual_room_id.total_rooms_count)
        if self.wmax_avail > max_avail:
            raise ValidationError("max avail for wubook can't be high \
                                                    than real availability")

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vals.update({'wpushed': False})
        return super(VirtualRoomAvailability, self).write(vals)

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


class HotelVirtualRoom(models.Model):
    _inherit = 'hotel.virtual.room'

    hcal_sequence = fields.Integer('Calendar Sequence', default=0)

    @api.multi
    def unlink(self):
        vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
        for record in self:
            pr_chached = vroom_pr_cached_obj.search([
                ('virtual_room_id', '=', record.id)
            ])
            #  Because 'pricelist.cached' is an isolated model,
            # doesn't trigger 'ondelete'. Need call 'unlink' instead.
            pr_chached.unlink()
        return super(HotelVirtualRoom, self).unlink()

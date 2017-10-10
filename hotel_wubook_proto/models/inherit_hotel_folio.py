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


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    @api.depends('whas_wubook_reservations', 'room_lines')
    def _has_wubook_reservations(self):
        if any(self.room_lines):
            for room in self.room_lines:
                if room.wrid != 'none':
                    self.whas_wubook_reservations = True
                    return
        self.whas_wubook_reservations = False

    wseed = fields.Char("WuBook Session Seed", readonly=True)
    wcustomer_notes = fields.Text("WuBook Customer Notes", readonly=True)
    whas_wubook_reservations = fields.Boolean(compute=_has_wubook_reservations,
                                              store=False)

    @api.multi
    def import_reservations(self):
        return self.env['wubook'].fetch_new_bookings()

    @api.multi
    def action_confirm(self):
        for rec in self:
            for room in rec.room_lines:
                room.to_read = False
        return super(HotelFolio, self).action_confirm()

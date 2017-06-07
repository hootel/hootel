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


class hotel_virtual_room(models.Model):
    _inherit = 'hotel.virtual.room'

    @api.depends('wpersons')
    def _get_persons(self):
        min = 0
        for rec in self:
            totals = rec.room_lines.mapped(lambda x: x.adults+x.children)
            _logger.info("PERSONAS")
            _logger.info(totals)
            rec.wpersons = 0

    wscode = fields.Char("WuBook Short Code")
    wrid = fields.Char("WuBook Room ID", readonly=True)
    wpersons = fields.Integer(compute=_get_persons, readonly=True)

    @api.model
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

    @api.multi
    def get_availability(self, date):
        folio_obj = self.env['hotel.folio']

        folios = folio_obj.search([('room_lines.checkin', '>=', date),
                                   ('room_lines.checkout', '<=', date),
                                   ('room_lines.id', 'in', self.room_ids.ids)])

        for folio in folios:
            for reserv in folios.room_lines:
                return True

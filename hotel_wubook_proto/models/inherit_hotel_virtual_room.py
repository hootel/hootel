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
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class HotelVirtualRoom(models.Model):
    _inherit = 'hotel.virtual.room'

    #@api.depends('wcapacity')
    @api.onchange('room_ids', 'room_type_ids')
    def _get_capacity(self):
        hotel_room_obj = self.env['hotel.room']
        for rec in self:
            room_categories = rec.room_type_ids.mapped('cat_id.id')
            room_ids = rec.room_ids + hotel_room_obj.search([('categ_id.id', 'in', room_categories)])
            capacities = room_ids.mapped('capacity')
            rec.wcapacity = any(capacities) and min(capacities) or 0

    wscode = fields.Char("WuBook Short Code", required=True, readonly=True)
    wrid = fields.Char("WuBook Room ID", readonly=True)
    wcapacity = fields.Integer(compute=_get_capacity, readonly=True, store=True)

    @api.multi
    @api.constrains('wscode')
    def _check_wscode(self):
        for record in self:
            if len(record.wscode) > 4:  # Wubook scode max. length
                raise ValidationError(_("SCODE Can't be longer than 4 characters"))

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True):
            wrid = self.env['wubook'].create_room(
                vals['name'],
                vals['wcapacity'],
                vals['list_price'],
                vals.get('max_real_rooms', 1)
            )
            vals.update({'wrid': wrid})
        return super(HotelVirtualRoom, self).create(vals)

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True):
            for record in self:
                self.env['wubook'].modify_room(vals.get('wrid', record.wrid),
                                               vals.get('name', record.name),
                                               vals.get('wcapacity', record.wcapacity),
                                               vals.get('list_price', record.list_price),
                                               vals.get('max_real_rooms', record.max_real_rooms),
                                               vals.get('wscode', record.wscode))
        return super(HotelVirtualRoom, self).write(vals)

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True):
            for record in self:
                self.env['wubook'].delete_plan(record.wpid)
        return super(HotelVirtualRoom, self).unlink()

    @api.multi
    def import_rooms(self):
        wubook = self.env['wubook']
        wubook.import_rooms()
        return True

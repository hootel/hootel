# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <alex@aloxa.eu>
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


class HotelVirtualRoomAvailability(models.Model):
    _inherit = 'mail.thread'
    _name = 'hotel.virtual.room.availability'

    virtual_room_id = fields.Many2one('hotel.virtual.room', 'Virtual Room',
                                      required=True, track_visibility='always',
                                      ondelete='cascade')
    avail = fields.Integer('Avail', default=0, track_visibility='always')
    no_ota = fields.Boolean('No OTA', default=False, track_visibility='always')
    booked = fields.Boolean('Booked', default=False, readonly=True,
                            track_visibility='always')
    date = fields.Date('Date', required=True, track_visibility='always')

    @api.constrains('avail')
    def _check_avail(self):
        if self.avail < 0:
            raise ValidationError("avail can't be less than zero")

    @api.constrains('date', 'virtual_room_id')
    def _check_date_virtual_room_id(self):
        count = self.search_count([
            ('date', '=', self.date),
            ('virtual_room_id', '=', self.virtual_room_id.id)
        ])
        if count > 1:
            raise ValidationError("can't assign the same date to more than \
                                    one virtual room")

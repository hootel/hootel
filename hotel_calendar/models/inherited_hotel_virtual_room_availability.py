# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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


class HotelVirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    @api.model
    def create(self, vals):
        res = super(HotelVirtualRoomAvailability, self).create(vals)
        self.env['bus.hotel.calendar'].send_availability_notification({
            'date': res.date,
            'avail': res.avail,
            'no_ota': res.no_ota,
            'virtual_room_id': res.virtual_room_id.id,
            'id': res.id,
        })
        return res

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelVirtualRoomAvailability, self).write(vals)
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for record in self:
            bus_hotel_calendar_obj.send_availability_notification({
                'date': record.date,
                'avail': record.avail,
                'no_ota': record.no_ota,
                'virtual_room_id': record.virtual_room_id.id,
                'id': record.id,
            })
        return ret_vals

    @api.multi
    def unlink(self):
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            unlink_vals.append({
                'date': record.date,
                'avail': record.virtual_room_id.max_real_rooms,
                'virtual_room_id': record.virtual_room_id.id,
                'no_ota': False,
                'id': record.id,
            })
        res = super(HotelVirtualRoomAvailability, self).unlink()
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for uval in unlink_vals:
            bus_hotel_calendar_obj.send_availability_notification(uval)
        return res

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
import logging
_logger = logging.getLogger(__name__)


class HotelVirtualRoomResrtrictionItem(models.Model):
    _inherit = 'hotel.virtual.room.restriction.item'

    @api.model
    def create(self, vals):
        res = super(HotelVirtualRoomResrtrictionItem, self).create(vals)
        restrictions_parity_id = self.env['ir.values'].sudo().get_default(
                        'hotel.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        restriction_id = res.restriction_id.id
        if restriction_id == restrictions_parity_id and \
                self.applied_on == '0_virtual_room':
            self.env['bus.hotel.calendar'].send_restriction_notification({
                'restriction_id': self.restriction_id.id,
                'date': self.date_start,
                'min_stay': self.min_stay,
                'min_stay_arrival': self.min_stay_arrival,
                'max_stay': self.max_stay,
                'closed': self.closed,
                'closed_departure': self.closed_departure,
                'closed_arrival': self.closed_arrival,
                'virtual_room_id': self.virtual_room_id.id,
                'id': self.id,
            })
        return res

    @api.multi
    def write(self, vals):
        restrictions_parity_id = self.env['ir.values'].sudo().get_default(
                        'hotel.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        ret_vals = super(HotelVirtualRoomResrtrictionItem, self).write(vals)

        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for record in self:
            if record.restriction_id.id != restrictions_parity_id or \
                    record.applied_on != '0_virtual_room':
                continue
            bus_hotel_calendar_obj.send_restriction_notification({
                'restriction_id': record.restriction_id.id,
                'date': record.date_start,
                'min_stay': record.min_stay,
                'min_stay_arrival': record.min_stay_arrival,
                'max_stay': record.max_stay,
                'closed': record.closed,
                'closed_departure': record.closed_departure,
                'closed_arrival': record.closed_arrival,
                'virtual_room_id': record.virtual_room_id.id,
                'id': record.id,
            })
        return ret_vals

    @api.multi
    def unlink(self):
        restrictions_parity_id = self.env['ir.values'].sudo().get_default(
                        'hotel.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            if record.restriction_id.id != restrictions_parity_id or \
                    record.applied_on != '0_virtual_room':
                continue
            unlink_vals.append({
                'restriction_id': record.restriction_id.id,
                'date': record.date_start,
                'min_stay': 0,
                'min_stay_arrival': 0,
                'max_stay': 0,
                'closed': False,
                'closed_departure': False,
                'virtual_room_id': record.virtual_room_id.id,
                'id': record.id,
            })
        res = super(HotelVirtualRoomResrtrictionItem, self).unlink()
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for uval in unlink_vals:
            bus_hotel_calendar_obj.send_restriction_notification(uval)
        return res

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


class HotelConfiguration(models.TransientModel):
    _inherit = 'hotel.config.settings'

    divide_rooms_by_capacity = fields.Boolean('Divide rooms by capacity')
    end_day_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='End day of week', default='6', required=True)
    type_move = fields.Selection([
        ('normal', 'Normal'),
        ('assisted', 'Assisted'),
        ('allow_invalid', 'Allow Invalid')
    ], string='Reservation move mode', default='normal', required=True)
    default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month', required=True)


    @api.multi
    def set_divide_rooms_by_capacity(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'divide_rooms_by_capacity', self.divide_rooms_by_capacity)

    @api.multi
    def set_end_day_week(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'end_day_week', self.end_day_week)

    @api.multi
    def set_type_move(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'type_move', self.type_move)

    @api.multi
    def set_default_num_days(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_num_days', self.default_num_days)

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
from openerp import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    pms_divide_rooms_by_capacity = fields.Boolean('Divide rooms by capacity')
    pms_end_day_week = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='End day of week', default='6')
    pms_end_day_week_offset = fields.Selection([
        ('0', '0 Days'),
        ('1', '1 Days'),
        ('2', '2 Days'),
        ('3', '3 Days'),
        ('4', '4 Days'),
        ('5', '5 Days'),
        ('6', '6 Days')
    ], string='Also illuminate the previous', default='0')
    pms_type_move = fields.Selection([
        ('normal', 'Normal'),
        ('assisted', 'Assisted'),
        ('allow_invalid', 'Allow Invalid')
    ], string='Reservation move mode', default='normal')
    pms_default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month')

    pms_show_notifications = fields.Boolean('Show Notifications', default=True)
    pms_show_pricelist = fields.Boolean('Show Pricelist', default=True)
    pms_show_availability = fields.Boolean('Show Availability', default=True)
    pms_show_num_rooms = fields.Integer('Show Num. Rooms', default=0)

    pms_allowed_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Allow Calander Event Tags")
    pms_denied_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Deny Calander Event Tags")

    npms_end_day_week = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='End day of week', default='6')
    npms_end_day_week_offset = fields.Selection([
        ('0', '0 Days'),
        ('1', '1 Days'),
        ('2', '2 Days'),
        ('3', '3 Days'),
        ('4', '4 Days'),
        ('5', '5 Days'),
        ('6', '6 Days')
    ], string='Also illuminate the previous', default='0')
    npms_default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month')

    npms_allowed_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Allow Calander Event Tags")
    npms_denied_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Deny Calander Event Tags")

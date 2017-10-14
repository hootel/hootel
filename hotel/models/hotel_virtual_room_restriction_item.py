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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class HotelVirtualRoomRestrictionItem(models.Model):
    _name = 'hotel.virtual.room.restriction.item'

    restriction_id = fields.Many2one('hotel.virtual.room.restriction', 'Restriction Plan', ondelete='cascade', select=True)
    virtual_room_id = fields.Many2one('hotel.virtual.room', 'Virtual Room')
    date_start = fields.Date('From')
    date_end = fields.Date("To")
    applied_on = fields.Selection([
        ('1_global', 'Global'),
        ('0_virtual_room', 'Virtual Room')], string="Apply On", required=True,
        help='Pricelist Item applicable on selected option')

    min_stay = fields.Integer("Min. Stay")
    min_stay_arrival = fields.Integer("Min. Stay Arrival")
    max_stay = fields.Integer("Max. Stay")
    closed = fields.Boolean('Closed')
    closed_departure = fields.Boolean('Closed Departure')
    closed_arrival = fields.Boolean('Closed Arrival')

    @api.constrains('min_stay', 'min_stay_arrival', 'max_stay')
    def _check_min_stay_min_stay_arrival_max_stay(self):
        if self.min_stay < 0:
            raise ValidationError("Min. Stay can't be less than zero")
        elif self.min_stay_arrival < 0:
            raise ValidationError("Min. Stay Arrival can't be less than zero")
        elif self.max_stay < 0:
            raise ValidationError("Max. Stay can't be less than zero")

    @api.constrains('date_start', 'date_end')
    def _check_date_start_date_end(self):
        if self.applied_on == '1_global':
            self.date_start = False
            self.date_end = False
        elif self.date_start and self.date_end:
            date_start_dt = datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT)
            date_end_dt = datetime.strptime(self.date_end, DEFAULT_SERVER_DATE_FORMAT)
            if date_end_dt < date_start_dt:
                raise ValidationError("Invalid Dates")

    @api.constrains('applied_on')
    def _check_applied_on(self):
        count = self.search_count([('applied_on', '=', '1_global')])
        if count > 1:
            raise ValidationError("Already exists an global rule")

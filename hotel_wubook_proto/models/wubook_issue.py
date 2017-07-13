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


class WuBookIssue(models.Model):
    _inherit = ['ir.needaction_mixin']
    _name = 'wubook.issue'

    section = fields.Selection([
        ('wubook', 'WuBook'),
        ('reservation', 'Reservation'),
        ('rplan', 'Restriction Plan'),
        ('plan', 'Price Plan'),
        ('room', 'Room'),
        ('avail', 'Availability')], required=True)
    to_read = fields.Boolean("To Read", default=True)
    message = fields.Char("Internal Message")
    wid = fields.Char("WuBook ID")
    wmessage = fields.Char("WuBook Message")

    @api.multi
    def mark_readed(self):
        for record in self:
            record.to_read = False

    @api.multi
    def toggle_to_read(self):
        for record in self:
            record.to_read = not record.to_read

    @api.model
    def _needaction_domain_get(self):
        return [('to_read', '=', True)]

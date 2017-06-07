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
from openerp.exceptions import except_orm, UserError, ValidationError


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    wrid = fields.Char("WuBook Reservation ID", default="none", readonly=True)
    wota = fields.Boolean("WuBook OTA", default=False, readonly=True)

#     @api.model
#     def create(self, vals, check=True):
#         if check:
#             vals = self.env['wubook'].create_reservation(vals)
#         return super(HotelReservation, self).create(vals)
# 
#     @api.multi
#     def write(self, vals):
#         ret_vals = super(HotelReservation, self).write(vals)
#         for record in self:
#             if not record.wota:
#                 self.env['wubook'].cancel_reservation(record.id, 'Modificated by admin')
#                 self.env['wubook'].create_reservation(record.id)
#         return ret_vals

#     @api.multi
#     def unlink(self):
#         for record in self:
#             if not self.wota:
#                 self.env['wubook'].cancel_reservation(record.id, 'Cancelled by admin')

#         return super(HotelReservation, self).unlink()

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

    @api.model
    def create(self, vals):
        ret_vals = super(HotelReservation, self).create(vals)
        partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
        notification = {
            'type': 'reservation',
            'subtype': 'created',
            'name': partner_id and partner_id.name,
        }
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation', self.env.uid), notification)
        return ret_vals

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelReservation, self).write(vals)
        partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
        notification = {
            'type': 'reservation',
            'subtype': 'write',
            'name': partner_id.name,
        }
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation', self.env.uid), notification)
        return ret_vals

    @api.multi
    def unlink(self):
        notification = {
            'type': 'reservation',
            'subtype': 'unlink',
            'name': self.partner_id.name,
        }
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation', self.env.uid), notification)
        return super(HotelReservation, self).unlink()

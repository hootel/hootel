# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------
from openerp import models, fields, api, _

class ResPartner(models.Model):

    _inherit = 'res.partner'

    reservations_count = fields.Integer('Reservations', compute='_compute_reservations_count')
    folios_count = fields.Integer('Folios', compute='_compute_folios_count')

    def _compute_reservations_count(self):
        for partner in self:
            partner.reservations_count = self.env['hotel.reservation'].search_count([('partner_id.id','=',partner.id)])

    def _compute_folios_count(self):
        for partner in self:
            partner.folios_count = self.env['hotel.folio'].search_count([('partner_id.id','=',partner.id)])



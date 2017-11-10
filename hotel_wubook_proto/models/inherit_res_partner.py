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


class ResPartner(models.Model):
    _inherit='res.partner'

    unconfirmed = fields.Boolean('Unconfirmed', default=False)

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        new_vat = vals.get('vat')
        if new_vat:
            org_partner_id = self.env['res.partner'].search([('vat', '=', new_vat)], limit=1)
            if org_partner_id:
                for record in self:
                    if record.unconfirmed:
                        folio_ids = self.env['hotel.folio'].search([('partner_id', '=', record.id)])
                        if folio_ids:
                            folio_ids.write({'partner_id': org_partner_id.id})
                        record.unlink()
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.partner',
                    'views': [[False, "form"]],
                    'target': 'current',
                    'res_id': org_partner_id.id,
                }
        return res

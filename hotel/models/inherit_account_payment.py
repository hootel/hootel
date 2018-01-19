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
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
from decimal import Decimal
import datetime
import urllib2
import time
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    folio_id = fields.Many2one('hotel.folio', string='Folio')
    amount_total_folio = fields.Float(
        compute="_compute_folio_amount", store=True,
        string="Total amount in folio",
    )

    @api.multi
    @api.depends('state')
    def _compute_folio_amount(self):
        res = []
        fol = ()
        for payment in self:
            amount_pending = 0
            total_amount = 0
            if payment.invoice_ids and not payment.folio_id:
############# It's necesary becouse invoice_ids in folio (sale_order) is compute (can't search)
                folios = self.env['hotel.folio'].search([
                    ('partner_id', '=', payment.partner_id.id)
                ])
                for rec in folios:
                    for inv in rec.invoice_ids:
                        if inv.id in payment.invoice_ids.ids:
                            fol = self.env['hotel.folio'].search([
                                ('id', '=', rec.id)
                            ])
#############                            
            elif payment.folio_id:
                fol = payment.env['hotel.folio'].search([
                    ('id', '=', payment.folio_id.id)
                ])
            else:
                return
            # We must pay only one folio
            if len(fol) == 0:
                return
            elif len(fol) > 1:
                raise except_orm(_('Warning'), _('This pay is related with \
                                                more than one Reservation.'))
            else:
                payment.write({'folio_id': fol.id})
                total_folio = fol.amount_total
                payments = payment.env['account.payment'].search([
                    '|', ('folio_id', '=', fol.id),
                    ('invoice_ids', 'in', fol.invoice_ids.ids),
                    ('payment_type', '=', 'inbound'),
                    ('state', '=', 'posted')
                ])
                total_amount = sum(pay.amount for pay in payments)
                if total_amount < total_folio:
                    amount_pending = total_folio - total_amount
                paid = total_folio - amount_pending
                fol.write({'invoices_amount': amount_pending})
                fol.write({'invoices_paid': paid})
                payment.amount_total_folio = total_folio
                res += payment
            return res

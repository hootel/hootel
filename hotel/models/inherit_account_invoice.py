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
from openerp.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        cr, uid, context = self.env.args
        context = dict(context)
        if context.get('invoice_origin', False):
            vals.update({'origin': context['invoice_origin']})
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def action_folio_payments(self):
        self.ensure_one()
        sales = self.mapped('invoice_line_ids.sale_line_ids.order_id')
        folios = self.env['hotel.folio'].search([('id','in',sales.ids)])
        payments_obj = self.env['account.payment']
        payments = payments_obj.search([('folio_id','in',folios.ids)])
        payment_ids = payments.mapped('id')
        return{
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', payment_ids)],
        }
        
    # ~ @api.one
    # ~ @api.depends(
    #     ~ 'amount_total',
    #     ~ 'invoice_line_ids.price_subtotal',
    #     ~ 'move_id.line_ids.amount_residual',
    #     ~ 'move_id.line_ids.currency_id')
    # ~ def change_sale_amount(self):
    #     ~ _logger.info("DEPENDDDSSSSS")
    #     ~ for inv in self:
    #         ~ folios = self.env['hotel.folio'].search([('id','in',sale_ids)])
    #         ~ _logger.info("FOLIOS CAMBIADOS DESDE LA FACTURA:")
    #         ~ _logger.info(folios)


    dif_customer_payment = fields.Boolean(compute='_compute_dif_customer_payment')
    sale_ids = fields.Many2many(
            'sale.order', 'sale_order_invoice_rel', 'invoice_id',
            'order_id', 'Sale Orders', readonly=True,
            help="This is the list of sale orders related to this invoice.")

    @api.multi
    def _compute_dif_customer_payment(self):
        for inv in self:
            sales = inv.mapped('invoice_line_ids.sale_line_ids.order_id')
            folios = inv.env['hotel.folio'].search([('id','in',sales.ids)])
            payments_obj = inv.env['account.payment']
            payments = payments_obj.search([('folio_id','in',folios.ids)])
            for pay in payments:
                if pay.partner_id <> inv.partner_id:
                    inv.dif_customer_payment = True

    @api.multi
    def action_invoice_open(self):
        to_open_invoices_without_vat = self.filtered(lambda inv: inv.state != 'open' and inv.partner_id.vat == False)
        if to_open_invoices_without_vat:
            vat_error = _("We need the VAT of the following companies")
            for invoice in to_open_invoices_without_vat:
                vat_error += ", " + invoice.partner_id.name
            raise ValidationError(vat_error)
        return super(AccountInvoice, self).action_invoice_open()

    # ~ @api.multi
    # ~ def confirm_paid(self):
    #     ~ '''
    #     ~ This method change pos orders states to done when folio invoice
    #     ~ is in done.
    #     ~ ----------------------------------------------------------
    #     ~ @param self: object pointer
    #     ~ '''
    #     ~ pos_order_obj = self.env['pos.order']
    #     ~ res = super(AccountInvoice, self).confirm_paid()
    #     ~ pos_odr_rec = pos_order_obj.search([('invoice_id', 'in', self._ids)])
    #     ~ pos_odr_rec and pos_odr_rec.write({'state': 'done'})
    #     ~ return res
    

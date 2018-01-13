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

    sale_ids = fields.Many2many(
            'sale.order', 'sale_order_invoice_rel', 'invoice_id',
            'order_id', 'Sale Orders', readonly=True,
            help="This is the list of sale orders related to this invoice.")


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

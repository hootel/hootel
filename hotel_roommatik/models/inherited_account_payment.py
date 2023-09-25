# Copyright 2017  Dario Lodeiros
# Copyright 2020  Jose Luis Algara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# from odoo.exceptions import except_orm
from odoo import models, api
import logging


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def rm_add_payment(self, code, payment):
        _logger = logging.getLogger(__name__)
        res_company_obj = self.env.user.company_id
        reservation = self.env['hotel.reservation'].search([
            '|', ('localizator', '=', code),
            ('folio_id.name', '=', code)])
        if not reservation:
            return False
        if (res_company_obj.rm_cash_journal.id == 0 or
                res_company_obj.rm_cash_journal.id == 0):
            _logger.critical("RoomMatik CONFIG ERROR need Journal IDs")
            return False
        if reservation:
            for cashpay in payment['CashPayments']:
                _logger.info("RoomMatik Payment Cash in Folio: [%s] of %s",
                             reservation.folio_id,
                             cashpay['Amount'].replace(',', '.'))
                vals = {
                    'journal_id': res_company_obj.rm_cash_journal.id,  # 7
                    'partner_id': reservation.partner_invoice_id.id,
                    'amount': float(cashpay['Amount'].replace(',', '.')),
                    'payment_date': cashpay['DateTime'],
                    'communication': reservation.name,
                    'folio_id': reservation.folio_id.id,
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'state': 'draft',
                }
                pay = self.create(vals)
            for cashpay in payment['CreditCardPayments']:
                _logger.info("RoomMatik Payment C.Card in Folio: [%s] of %s",
                             reservation.folio_id,
                             cashpay['Amount'].replace(',', '.'))
                vals = {
                    'journal_id': res_company_obj.rm_credit_journal.id,  # 15
                    'partner_id': reservation.partner_invoice_id.id,
                    'amount': float(cashpay['Amount'].replace(',', '.')),
                    'payment_date': cashpay['DateTime'],
                    'communication': reservation.name,
                    'folio_id': reservation.folio_id.id,
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'state': 'draft',
                }
                pay = self.create(vals)
        pay.post()
        return True

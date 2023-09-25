# Copyright 2020  Jose Luis Algara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api
import logging
import datetime
import json


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def fc_add_payment(self, code, amount, journal, name):
        _logger = logging.getLogger(__name__)
        res_company_obj = self.env.user.company_id

        # Search by reservation ID
        reservation = self.env['hotel.reservation'].search([('id', '=', code)])

        if not reservation or journal < 1 or journal > 2:
            _logger.error("FastCheckin ERROR in payment paramenter")
            return False
        if res_company_obj.fc_credit_journal.id == 0 and journal == 1:
            _logger.error("FastCheckin CONFIG ERROR need Credit Journal ID")
            return False
        if res_company_obj.fc_cash_journal.id == 0 and journal == 2:
            _logger.error("FastCheckin CONFIG ERROR need cash Journal ID")
            return False
        pay_date = datetime.datetime.now()
        _logger.info("%s Payment in [%s] of %s€ in journal [%s]",
                     name,
                     reservation.folio_id.name,
                     amount,
                     journal)
        journal = res_company_obj.fc_credit_journal.id if journal == 1 else res_company_obj.fc_cash_journal.id

        vals = {
            'journal_id': journal,
            'partner_id': reservation.partner_invoice_id.id,
            'amount': float(amount.replace(',', '.')),
            'payment_date': pay_date,
            'communication': name + " para: " + reservation.name,
            'folio_id': reservation.folio_id.id,
            'payment_type': 'inbound',
            'payment_method_id': 1,
            'partner_type': 'customer',
            'state': 'draft',
        }
        pay = self.create(vals)
        pay.post()
        json_response = []
        json_response.append([{
            'amount': pay.amount,
            'communication': pay.communication,
            'id': pay.id,
            'pay_name': pay.display_name
            }])
        return json.dumps(json_response)

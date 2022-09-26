# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import except_orm
from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    validated = fields.Boolean(string='Validado', default=False)

    @api.multi
    def validate(self):
        for record in self:
            record.validated = not record.validated

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
from openerp import models, fields, api, _


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    @api.multi
    @api.depends('state')
    def _compute_folio_amount(self):
        payments = super(AccountPayment, self)._compute_folio_amount()
        if payments:
            for pay in payments:
                if pay.folio_id:
                    fol = pay.env['hotel.folio'].search([
                        ('id', '=', pay.folio_id.id)
                    ])
                else:
                    return
                # We must pay only one folio
                if len(fol) == 0:
                    return
                elif len(fol) > 1:
                    raise except_orm(_('Warning'), _('This pay is related \
                                            with more than one Reservation.'))
                else:
                    fol.room_lines._compute_color()

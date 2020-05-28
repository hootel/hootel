# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
import re
from openerp.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    limit_night_sale = fields.Char('Allow night sale until...',
                                   help="HH:mm Format", default="9:00")

    @api.constrains('limit_night_sale',)
    def _check_hours(self):
        r = re.compile('[0-2][0-9]:[0-5][0-9]')
        if not r.match(self.limit_night_sale):
            raise ValidationError(_("Invalid limit hour (Format: HH:mm)"))

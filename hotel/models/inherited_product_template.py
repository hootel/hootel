# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    per_day = fields.Boolean('Unit increment per day')
    per_person = fields.Boolean('Unit increment per person')
    daily_limit = fields.Integer('Daily limit')
    is_extra_bed = fields.Boolean('Is extra bed', default=False)
    is_popoverable = fields.Boolean('Show in Popover', default=False,
                                    help='Specifies if the product is shown in the popover information.')

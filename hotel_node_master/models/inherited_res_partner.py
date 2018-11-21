# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    partner_binding_ids = fields.One2many('node.res.partner', 'odoo_id',
                                          'Node Partners binded to this one')

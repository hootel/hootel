# -*- coding: utf-8 -*-

from openerp import models, fields, api

class category_tourism(models.Model):
    _name = 'category'

    name = fields.Char('Category', required=True)
    tipo = fields.Char('Category type', required=True)
   
    @api.multi
    def name_get(self):
        data = []
        for record in self:
            display_value = record.tipo + " (" + record.name + ") "
            data.append((record.id, display_value))
        return data
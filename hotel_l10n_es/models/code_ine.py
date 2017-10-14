#-*- coding: utf-8 -*- 

from openerp import models, fields, api

class IneCode(models.Model):
    _name = 'code_ine'

    name = fields.Char('Place', required=True)
    code = fields.Char('Code', required=True)
 
    @api.multi
    def name_get(self):
        data = []
        for record in self:
            subcode = record.code
            if len(record.code)>3:
                subcode = 'ESP'
            display_value = record.name + " (" + subcode + ")"
            data.append((record.id, display_value))
        return data
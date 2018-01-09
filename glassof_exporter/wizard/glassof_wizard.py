# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception,
                                                content_disposition
from odoo import api, fields, models


# WUBOOK
class GlassofExporterWizard(models.TransientModel):
    FILENAME = 'glassof.xls'
    _name = 'glassof.exporter.wizard'

    @api.model
    def export(self, filename=False):
        filecontent = False
        if not filecontent:
            return request.not_found()
        return request.make_response(filecontent,
                    [('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', content_disposition(self.FILENAME))])

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
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
from openerp import models, fields, api
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
import xlsxwriter
from cStringIO import StringIO
import base64  


class Wizard(models.TransientModel):
    FILENAME = 'revenue.xls'
    _name = 'revenue.exporter.wizard'

    room_type = fields.Char()
    date_1 = fields.Date()
    date_2 = fields.Date()
    period_1 = fields.Date()
    period_2 = fields.Date()
    txt_filename = fields.Char()
    txt_binary = fields.Binary()

    @api.one
    def export(self):

        file_data = StringIO()
        workbook = xlsxwriter.Workbook(file_data)
        # Create a workbook and add a worksheet.
        #workbook = xlsxwriter.Workbook('/tmp/export.xlsx')
        worksheet = workbook.add_worksheet()

        # Some data we want to write to the worksheet.
        expenses = (
            ['Rent', 1000],
            ['Gas',   100],
            ['Food',  300],
            ['Gym',    50],
        )

        # Start from the first cell. Rows and columns are zero indexed.
        row = 0
        col = 0

        # Iterate over the data and write it out row by row.
        for item, cost in (expenses):
            worksheet.write(row, col,     item)
            worksheet.write(row, col + 1, cost)
            row += 1

        # Write a total using a formula.
        worksheet.write(row, 0, 'Total')
        worksheet.write(row, 1, '=SUMA(B1:B4)')

        # Write file in tmp
        workbook.close()

        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------

        content ="hola"
        content += """
"""


        file_data.seek(0)
        #return (file_data.read(), 'xlsx')
        return self.write({
            'txt_filename': 'revenue.'+ fields.Date.today() +'.xlsx',
            'txt_binary': base64.encodestring(file_data.read())
            #'txt_binary': base64.encodestring("file_data.read()")
            })


            

    

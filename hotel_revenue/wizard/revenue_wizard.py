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
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from cStringIO import StringIO
import xlsxwriter
import base64


class Wizard(models.TransientModel):
    FILENAME = 'revenue.xls'
    _name = 'revenue.exporter.wizard'

    room_type_id = fields.Many2one('hotel.room.type',string='Room Type')
    date_1 = fields.Date('PickUp start date',default=fields.Date.today())
    date_2 = fields.Date('PickUp end date',default=date.today() + timedelta(days=1))
    period_1 = fields.Date('Start period',default=fields.Date.today())
    period_2 = fields.Date('End period',default=date.today() + relativedelta(months=3))
    txt_filename = fields.Char()
    txt_binary = fields.Binary()

    @api.one
    def export(self):

        # Create a workbook and add a worksheet.
        file_data = StringIO()
        #workbook = xlsxwriter.Workbook('/tmp/export.xlsx')
        workbook = xlsxwriter.Workbook(file_data)
        worksheet = workbook.add_worksheet()

        row = 2
        col = 0
        worksheet.write(0, col+0, 'Date')
        worksheet.write(0, col+1, 'Price')
        worksheet.write(0, col+2, 'Id')
        worksheet.write(0, col+3, 'State')
        worksheet.write(0, col+4, 'Type')
        worksheet.write(0, col+5, 'Ficha')
        worksheet.write(0, col+6, 'Checkin')
        worksheet.write(0, col+7, 'Checkout')
        worksheet.write(0, col+8, 'Type')
        worksheet.write(0, col+9, 'Created')
        worksheet.write(0, col+10, 'Created')
        worksheet.write(0, col+11, 'Updated')
        worksheet.write(0, col+12, 'Name')
        worksheet.write(0, col+13, 'Room')
        worksheet.write(0, col+14, 'cat_id')

        # Seleccionamos dentro del periodo, las normales y no canceladas filtrando por tipo de habitación.
        if self.room_type_id.code_type == False:
            lines_res = self.env['hotel.reservation.line'].search(['&','&','&',
                ('date', '>=', self.period_1), ('date', '<=', self.period_2),
                ('reservation_id.reservation_type', '=','normal'),
                ('reservation_id.state', '<>','cancelled')
                ] , order="date" )
        else:
            lines_res = self.env['hotel.reservation.line'].search(['&','&','&','&',
                ('date', '>=', self.period_1), ('date', '<=', self.period_2),
                ('reservation_id.reservation_type', '=','normal'),
                ('reservation_id.state', '<>','cancelled'),
                ('reservation_id.product_id.categ_id.id', '=',self.room_type_id.cat_id.id)
                ] , order="date" )

        for line in lines_res:
            room = self.env['hotel.room'].search([('product_id','=',line.reservation_id.product_id.id)])

            worksheet.write(row, col+0, line.date)
            worksheet.write(row, col+1, line.price)
            worksheet.write(row, col+2, line.reservation_id.id)
            worksheet.write(row, col+3, line.reservation_id.state)
            worksheet.write(row, col+4, line.reservation_id.reservation_type)
            #worksheet.write(row, col+5, line.reservation_id.folio_id)
            worksheet.write(row, col+6, line.reservation_id.checkin)
            worksheet.write(row, col+7, line.reservation_id.checkout)
            #worksheet.write(row, 8, line.reservation_id.room_type_id)
            worksheet.write(row, col+9, line.create_date)
            worksheet.write(row, col+10, line.reservation_id.create_date)
            worksheet.write(row, col+11, line.write_date)
            worksheet.write(row, col+12, line.reservation_id.partner_id.name)
            worksheet.write(row, col+13, room.display_name)
            worksheet.write(row, col+14, line.reservation_id.product_id.categ_id.display_name)
            worksheet.write(row, col+15, line.reservation_id.product_id.categ_id.id)
            row += 1

        # Debug Stop -------------------
        #    import wdb; wdb.set_trace()
        # Debug Stop -------------------


        # Write file in tmp
        workbook.close()

        file_data.seek(0)
        return self.write({
            'txt_filename': 'revenue-'+ fields.Date.today() +'.xlsx',
            'txt_binary': base64.encodestring(file_data.read())
            })


            

    

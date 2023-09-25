# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2019 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
from io import BytesIO
from datetime import datetime, date
from odoo import api, fields, models, _
import xlsxwriter
import base64


class KellysWizard(models.TransientModel):
    _name = 'kellysreport'

    @api.model
    def _get_default_date(self):
        return date.today()

    def _get_default_habitaciones(self):
        return self.calculalimpiar(datetime.now())

    date_start = fields.Date("Fecha del listado", default=_get_default_date)
    habitaciones = fields.Many2many('kellysrooms', string="Limpieza:",
                                    default=_get_default_habitaciones)
    order = fields.Selection([
        ('kelly ASC', 'Calendario'),
        ('kelly ASC, tipo ASC', 'Limpiar como... y orden en el Calendario'),
        ('kelly ASC, tipo ASC, checkin ASC',
         'Limpiar como... y Hora de entrada'),
        ], 'Orden de impresión',
        default='kelly ASC, tipo ASC, checkin ASC',
        required=True,
        help='Establece el orden en el que se imprimira el listado')

    xls_filename = fields.Char()
    xls_binary = fields.Binary("Export data")

    @api.multi
    def calculate_report(self):
        self.habitaciones = self.calculalimpiar(
            datetime.strptime(self.date_start, "%Y-%m-%d"))
        return

    @api.multi
    def calculalimpiar(self, fechalimpieza=datetime.now()):
        dates = datetime.strftime(fechalimpieza, "%Y-%m-%d")
        grids = self.env['hotel.room'].search([], order='sequence ASC')
        grids2 = self.env['kellysrooms']
        listid = []
        for x in grids:
            rooms = self.env['hotel.reservation'].search(
                ['&', '&', ('checkin', '<=', dates),
                 ('checkout', '>=', dates),
                 ('state', '<>', 'cancelled'),
                 ('room_id', '=', x.id)
                 ], order='checkin ASC')

            tipos = False
            if len(rooms) != 0:
                if len(rooms) == 2:
                    tipos = 1
                    # Salida y etrada
                    checkinhour = rooms[1].checkin
                    checkouthour = rooms[1].checkout[:10]
                else:
                    if rooms[0].checkin[:10] == dates:
                        checkinhour = rooms[0].checkin
                        checkouthour = rooms[0].checkout[:10]
                        tipos = 3
                        # Revisar
                    elif rooms[0].checkout[:10] == dates:
                        checkinhour = 'no prevista'
                        checkouthour = ''
                        tipos = 1
                        # Salida
                    else:
                        checkinhour = rooms[0].checkin[:10]
                        checkouthour = rooms[0].checkout[:10]
                        tipos = 2
                        # Cliente
                        if rooms[0].reservation_type == 'staff':
                            checkinhour = rooms[0].checkin[:10]
                            checkouthour = rooms[0].checkout[:10]
                            tipos = 4
                            # Staff
                if rooms[0].reservation_type == 'out':
                    checkinhour = rooms[0].checkin[:10]
                    checkouthour = rooms[0].checkout[:10]
                    tipos = 5
                    # Averiada
            if tipos is not False:
                listid.append(grids2.create(
                    {'habitacion': rooms[0].room_id.name,
                     'habitacionid': rooms[0].room_id.id,
                     'tipo': tipos,
                     'notas': '',
                     'checkin': checkinhour,
                     # 'checkin': rooms[0].checkin[:10],
                     # 'checkout': rooms[0].checkout[:10],
                     'checkout': checkouthour,
                     # 'kelly': 5,
                     'clean_date': fechalimpieza
                     }).id)
        return self.env['kellysrooms'].search([('id', 'in', listid)])

    @api.multi
    def print_rooms_report(self):
        rooms = self.env['kellysrooms'].search([('id', 'in',
                                                 self.habitaciones.ids)],
                                               order=self.order)

        return self.env.ref(
                'kellys_daily_report.report_kellysrooms').report_action(rooms)

    @api.multi
    def _excel_export(self):
        tipo_limpieza = ['Salida', 'Cliente', 'Revisar', 'Staff', 'Averia']
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })
        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'Export Kellys Report from Odoo of ' + company_id.name,
            'author': 'Odoo',
            'manager': u'User',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'kellys, odoo, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })

        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC',
            'bold': True,
            'align': 'center'
        })

        worksheet = workbook.add_worksheet(_('Kellys Report'))

        worksheet.write('A1', _('Habitacion'), xls_cell_format_header)
        worksheet.write('B1', _('Tipo L.'), xls_cell_format_header)
        worksheet.write('C1', _('Notas'), xls_cell_format_header)
        worksheet.write('D1', _('Entrada'), xls_cell_format_header)
        worksheet.write('E1', _('Salida'), xls_cell_format_header)
        worksheet.write('F1', _('Asignado'), xls_cell_format_header)

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 30)

        rooms = self.env['kellysrooms'].search([('id', 'in',
                                                 self.habitaciones.ids)],
                                               order=self.order)

        offset = 1
        for k_room, v_room in enumerate(rooms):

            worksheet.write(k_room+offset, 0, v_room.habitacion)
            worksheet.write(k_room+offset, 1, tipo_limpieza[v_room.tipo-1])
            worksheet.write(k_room+offset, 2, v_room.notas)
            worksheet.write(k_room+offset, 3, v_room.checkin,
                            xls_cell_format_date)
            worksheet.write(k_room+offset, 4, v_room.checkout,
                            xls_cell_format_date)
            worksheet.write(k_room+offset, 5, v_room.kelly.name)

        workbook.close()
        file_data.seek(0)

        return {
            'xls_filename': 'Kellys_%s_%s.xlsx' % (
                self.env.user.company_id.property_name,
                self.date_start),
            'xls_binary': base64.encodestring(file_data.read()),
        }

    @api.multi
    def excel_rooms_report(self):
        self.write(self._excel_export())
        return {
            "type": "ir.actions.do_nothing",
        }

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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from cStringIO import StringIO
from random import randint
import xlsxwriter
import base64


def _offset_format_timestamp1(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, context=None):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the
    correct offset if both the server and local timeZone are recognized,or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they
    are both in the same TZ).

    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.

    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.

    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                # MODIFICAR CON EL TZ DEL HOTEL.................
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    # MODIFICAR CON EL TZ DEL HOTEL.................
                    dst_tz = pytz.timezone('UTC')
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
            res = dt_value.strptime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res




class Wizard(models.TransientModel):
    _name = 'revenue.exporter.wizard'

    @api.onchange('period_1')
    def validation_period_1(self):
        if self.period_2 <= self.period_1:
            self.period_2 = datetime.strptime(self.period_1,'%Y-%m-%d') + relativedelta(months=3)
            return {'warning': {'title': _('Error'), 'message': _('The beginning of the period can not be past the end of the period.'),},}

    @api.onchange('period_2')
    def validation_period_2(self):
        if self.period_2 <= self.period_1:
            self.period_1 = datetime.strptime(self.period_1,'%Y-%m-%d') + relativedelta(months=-3)
            return {'warning': {'title': _('Error'), 'message': _('The end of the period can not be before the beginning of the period.'),},}

    @api.onchange('date_1')
    def validation_date_1(self):
        if self.date_2 <= self.date_1:
            self.date_2 = datetime.strptime(self.date_1,'%Y-%m-%d') + timedelta(days=1)
            return {'warning': {'title': _('Error'), 'message': _('The date of the end of the PickUp can not be before the first PickUp date.'),},}

    @api.onchange('date_2')
    def validation_date_2(self):
        if self.date_2 <= self.date_1:
            self.date_1 = datetime.strptime(self.date_2,'%Y-%m-%d') + timedelta(days=-1)
            return {'warning': {'title': _('Error'), 'message': _('The date of the end of the PickUp can not be before the first PickUp date.'),},}


    #room_type_id = fields.Many2many('hotel.room.type',string='Room Type') #tomany
    room_type_id = fields.Many2many('hotel.room',string='Room Type') #tomany
    period_1 = fields.Date('Start period',default=fields.Date.today())
    period_2 = fields.Date('End period',default=date.today() + relativedelta(months=3))
    date_1 = fields.Date('PickUp start date',default=fields.Date.today())
    date_2 = fields.Date('PickUp end date',default=date.today() + timedelta(days=1))
    txt_filename = fields.Char()
    txt_msg = fields.Char()
    txt_binary = fields.Binary()

    @api.multi
    def export(self):
        self.ensure_one()
        if (self.period_1 <= self.date_1  < self.date_2 <= self.period_2):
            compan = self.env.user.company_id
            roomsxls = self.env['hotel.room'].search_count([])

            # Create a workbook and add a worksheet.
            file_data = StringIO()
            #workbook = xlsxwriter.Workbook('/tmp/export.xlsx')
            workbook = xlsxwriter.Workbook(file_data, {'strings_to_numbers': True, 'default_date_format': 'dd/mm/yyyy'})
            worksheet = workbook.add_worksheet(compan.property_name +' Data')

            workbook.set_properties({
            'title': 'Exported data from '+ compan.property_name,
            'subject': 'PMS Data from Odoo of '+ compan.property_name,
            'author': 'Odoo ALDA PMS',
            'manager': 'Jose Luis Algara',
            'company': compan.name,
            'category': 'Hoja de Calculo',
            'keywords': 'pms, odoo, alda, data, '+ compan.property_name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
            workbook.use_zip64()

            # cells formats definition
            date_format_xls = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss'})
            date_s_format_xls = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            date_sd_format_xls = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            date_sd_format_xls.set_pattern(1)
            date_sd_format_xls.set_bg_color('#2bc5d4')
            nume_format_xls = workbook.add_format({'num_format': '#,##0.00'})
            nume_e_format_xls = workbook.add_format({'num_format': u'#,##0.00€'})
            nume_p_format_xls = workbook.add_format({'num_format': u'0%'})
            nume_c_format_xls = workbook.add_format({'num_format': '[Green]General;[Red]-General;General'})
            nume_c_format_xls.set_align('center')
            nume_c_format_xls.set_font_size(12)
            nume_n_format_xls = workbook.add_format({'num_format': 'General'})
            nume_n_format_xls.set_align('center')
            cab_format_xls = workbook.add_format({'bold': True, 'font_color': '#5F5E97'})
            cab_format_xls.set_font_size(12)
            cab_format_xls.set_align('center')
            cab1_format_xls = workbook.add_format({'bold': True, 'font_color': '#5F5E97'})
            cab1_format_xls.set_font_size(13)

            row = 4
            col = 0
            worksheet.set_column(col, col+21, 11)
            worksheet.write(1, col+0, 'Periodo:', cab1_format_xls)
            worksheet.write(2, col+0, 'PickUp:', cab1_format_xls)
            worksheet.write(1, col+1, self.period_1+' a '+self.period_2, cab1_format_xls)
            worksheet.write(2, col+1, self.date_1+' hasta '+self.date_2, cab1_format_xls)

            worksheet.write(3, col+0, 'Fecha', cab_format_xls)
            worksheet.write(3, col+1, 'Pick Up', cab_format_xls)
            worksheet.write(3, col+2, 'R.Night', cab_format_xls)
            worksheet.write(3, col+3, u'% Ocup.', cab_format_xls)
            worksheet.write(3, col+4, 'Hab/Dia', cab_format_xls)
            worksheet.write(3, col+5, 'Cancel.', cab_format_xls)
            worksheet.write(3, col+6, u'Reve.€', cab_format_xls)
            worksheet.write(3, col+7, 'RevPAR', cab_format_xls)
            worksheet.write(3, col+8, 'ADR', cab_format_xls)

            # For UTC use take zone
            if self._context.get('tz'):
                to_zone = self._context.get('tz')
            else:
                to_zone = 'UTC'

            # Para cada dia del periodo...
            date_d = datetime.strptime(self.period_1,'%Y-%m-%d')
            delta = timedelta(days=1)
            while date_d <= datetime.strptime(self.period_2,'%Y-%m-%d'):
                if date_d.weekday() == 4 or date_d.weekday() == 5:
                    worksheet.write_datetime(row, col, date_d, date_sd_format_xls)
                else:
                    worksheet.write_datetime(row, col, date_d, date_s_format_xls)

                lines_res = self.env['hotel.reservation.line'].search(['&',
                    ('date', '=', date_d),
                    ('reservation_id.reservation_type', '=','normal'),
                    ] , order="date" )
                i = 1
                revenuxls = 0
                ardxls = 0
                ocupxls = 0
                r_nithxls = 0
                pickup_1xls = 0
                pickup_2xls = 0
                cancexls = 0
                roomxls = 0
                # descontamos las de Staff y out
                room_dia = roomsxls - self.env['hotel.reservation.line'].search_count(['&',
                    ('date', '=', date_d),
                    ('reservation_id.reservation_type', '<>','normal')])
                #para cada linea de reserva
                for line in lines_res:
                    #room = self.env['hotel.room'].search([('product_id','=',line.reservation_id.product_id.id)])
                    # Sumamos para el PickUp
                    if datetime.strptime(line.create_date[0:10],'%Y-%m-%d') <= datetime.strptime(self.date_1,'%Y-%m-%d'):
                        pickup_1xls +=1
                    if datetime.strptime(line.create_date[0:10],'%Y-%m-%d') <= datetime.strptime(self.date_2,'%Y-%m-%d'):
                        pickup_2xls +=1
                    # Si No esta cancelada sumamos revenue y ocupadas
                    if line.reservation_id.state <> "cancelled":
                        revenuxls += line.price
                        roomxls += 1
                        #worksheet.write_datetime(row, col+24+i, datetime.strptime(line.reservation_id.create_date,'%Y-%m-%d %H:%M:%S'), date_format_xls)
                        #worksheet.write_number(row, col+16+i, line.price, nume_format_xls)
                        #worksheet.write(row, col+8+i, line.reservation_id.state)
                        #i +=1
                    else:
                        # esta cancelada
                        cancexls +=1
                        # Restamos para el PickUp con fechas de reserva cancelada
                        if datetime.strptime(line.reservation_id.create_date[0:10],'%Y-%m-%d') <= datetime.strptime(self.date_1,'%Y-%m-%d'):
                            pickup_1xls -=1
                        if datetime.strptime(line.reservation_id.create_date[0:10],'%Y-%m-%d') <= datetime.strptime(self.date_2,'%Y-%m-%d'):
                            pickup_2xls -=1

                worksheet.write(row, col+1, pickup_2xls-pickup_1xls, nume_c_format_xls)
                worksheet.write_number(row, col+2, roomxls, nume_n_format_xls)
                ocupxls = roomxls/float(room_dia)
                worksheet.write_number(row, col+3, ocupxls, nume_p_format_xls)
                worksheet.write_number(row, col+4, room_dia, nume_n_format_xls)
                worksheet.write_number(row, col+5, cancexls, nume_n_format_xls)
                worksheet.write_number(row, col+6, revenuxls, nume_e_format_xls)
                ardxls = revenuxls/room_dia
                worksheet.write_number(row, col+7, ardxls, nume_e_format_xls)
                if roomxls > 0:
                    worksheet.write_number(row, col+8, (revenuxls/roomxls), nume_e_format_xls)


                # Debug Stop -------------------
                #import wdb; wdb.set_trace()
                # Debug Stop -------------------

                    #worksheet.write(row, col+6, line.reservation_id.product_id.categ_id.display_name)
                    #worksheet.write(row, col+9, line.reservation_id.product_id.categ_id.id)
                    #worksheet.write(row, col+10, self.room_type_id.cat_id.id)

                    #worksheet.write(row, col+11, tipos_seleccionados(self.room_type_id.cat_id))
                date_d += delta
                row += 1

            '''
            total_price_xls = 0
            for line in lines_res:
                room = self.env['hotel.room'].search([('product_id','=',line.reservation_id.product_id.id)])

                worksheet.write(row, col+0, line.date)
                worksheet.write_number(row, col+1, line.price, nume_format_xls)
                total_price_xls += line.price
                worksheet.write(row, col+2, line.reservation_id.id)
                worksheet.write(row, col+3, line.reservation_id.state)
                worksheet.write(row, col+4, line.reservation_id.reservation_type)
                #worksheet.write(row, col+5, line.reservation_id.folio_id)
                worksheet.write(row, col+16, line.reservation_id.checkin)
                worksheet.write(row, col+18, line.reservation_id.checkout)
                worksheet.write(row, col+17, line.reservation_id._get_checkin())
                worksheet.write(row, col+19, line.reservation_id._get_checkout_utc())
                #worksheet.write(row, 8, line.reservation_id.room_type_id)
                worksheet.write(row, col+9, line.create_date)
                worksheet.write_datetime(row, col+10, datetime.strptime(line.reservation_id.create_date,'%Y-%m-%d %H:%M:%S'), date_format_xls)
                worksheet.write_datetime(row, col+20, datetime.strptime(_offset_format_timestamp1(line.reservation_id.create_date,
                                                     '%Y-%m-%d %H:%M:%S',
                                                     '%Y-%m-%d %H:%M:%S',
                                                     ignore_unparsable_time=True,
                                                     context={'tz': to_zone}), '%Y-%m-%d %H:%M:%S'),
                                                 date_format_xls)
                worksheet.write_datetime(row, col+21, datetime.strptime(line.reservation_id.create_date,'%Y-%m-%d %H:%M:%S'), date_format_xls)
                worksheet.write(row, col+11, line.write_date)
                worksheet.write(row, col+12, line.reservation_id.partner_id.name)
                worksheet.write(row, col+13, room.display_name)
                worksheet.write(row, col+14, line.reservation_id.product_id.categ_id.display_name)
                worksheet.write(row, col+15, line.reservation_id.product_id.categ_id.id)
                row += 1
            worksheet.write(row+1, col+1, total_price_xls)
            worksheet.write_formula(row+2, col+1, '=SUM(B3:B'+str(row)+')')
            '''



            # Write file in tmp seek and insert in txt_binary
            workbook.close()

            file_data.seek(0)
            return self.write({
                'txt_filename': compan.property_name+'_'+ fields.Date.today() +'_'+ str(randint(100,999))+'.xlsx',
                'txt_msg': _('Download the file.'),
                'txt_binary': base64.encodestring(file_data.read()),
                })
        return self.write({
                'txt_msg': _('¡¡¡ Pickup date must be within the period.!!!'),
                })

def habitacionesdisponibles(self,dia=date.today()):


    #if tipo <> 0:
    #    lines = self.env['hotel.room'].search([('product_id','=',tipo)])
    #else:
    habit = []
    for a in self.room_type_id:
        habit.append(a.product_id.id)
    if len(habit) == 0:
        lines = self.env['hotel.room'].search([()])
    else:
        lines = self.env['hotel.room'].search([('product_id.id', 'in', habit)])
    # Debug Stop -------------------
    import wdb; wdb.set_trace()
    # Debug Stop -------------------
    #lines1 = self.env['hotel.room'].search([])

    lines_otras = self.env['hotel.reservation.line'].search(['&',
        ('date', '=', dia),
        ('reservation_id.reservation_type', '<>','normal')])



    return len(lines)-len(lines_otras)

def tipos_seleccionados(tipos):

    return ("55")


            # Debug Stop -------------------
            #    import wdb; wdb.set_trace()
            # Debug Stop -------------------

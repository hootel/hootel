# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alda Hotels <informatica@aldahotels.com>
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
from openerp import models, fields, api, _
from datetime import date, datetime, timedelta
import json


def get_years():
    """Return a year list, to select in year field."""
    year_list = []
    for i in range(2018, 2036):
        year_list.append((i, str(i)))
    return year_list


class Data_Bi(models.Model):
    """Management and export data for MopSolution MyDataBI."""

    _name = 'data_bi'

    # fecha Primer día del mes
    month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'),
                              (4, 'April'), (5, 'May'), (6, 'June'),
                              (7, 'July'), (8, 'August'), (9, 'September'),
                              (10, 'October'), (11, 'November'),
                              (12, 'December'), ],
                             string='Month', required=True)
    year = fields.Selection(get_years(), string='Year', required=True)
    room_nights = fields.Float("Room Nights", required=True, digits=(6, 2))
    # Número de Room Nights
    room_revenue = fields.Float("Room Revenue", required=True, digits=(6, 2))
    # Ingresos por Reservas
    estancias = fields.Integer("Number of Stays")  # Número de Estancias
    # ID_Tarifa numérico Código de la Tarifa
    # ID_Canal numérico Código del Canal
    # ID_Pais numérico Código del País
    # ID_Regimen numérico Cóigo del Régimen
    # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
    # iD_Segmento numérico Código del Segmento
    # ID_Cliente numérico Código del Cliente
    # Pension_Revenue numérico con dos decimales Ingresos por Pensión

    @api.model
    def export_data_bi(self,
                       archivo=False,
                       fechafoto=date.today().strftime('%Y-%m-%d')):
        u"""Prepare a Json Objet to export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        archivo = response file type
            archivo == 1 'Tarifa'
            archivo == 2 'Canal'
            archivo == 3 'Hotel'
            archivo == 4 'Pais'
            archivo == 5 'Regimen'
            archivo == 6 'Reservas'
            archivo == 7 'Capacidad'
            archivo == 8 'Tipo Habitación'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
        fechafoto = start date to take data
        """
        fechafoto = datetime.strptime(fechafoto, '%Y-%m-%d').date()
        # Change this to local test
        # fechafoto=date.today()
        # fechafoto=date(2018, 03, 01)

        if not isinstance(archivo, int):
            archivo = 0
        dic_param = []
        dic_param.append({'Archivo': archivo,
                          'Fechafoto': fechafoto.strftime('%Y-%m-%d')})
        compan = self.env.user.company_id
        dic_tarifa = []  # Diccionario con las tarifas
        tarifas = self.env['product.pricelist'].search_read([], ['name'])
        for tarifa in tarifas:
            dic_tarifa.append({'ID_Hotel': compan.id_hotel,
                               'ID_Tarifa': tarifa['id'],
                               'Descripcion': tarifa['name'].encode(
                                   'ascii', 'xmlcharrefreplace')})

        dic_canal = []  # Diccionario con los Canales
        canal_array = ['door', 'mail', 'phone', 'web']
        for i in range(0, len(canal_array)):
            dic_canal.append({'ID_Hotel': compan.id_hotel,
                              'ID_Canal': i,
                              'Descripcion': canal_array[i]})

        dic_hotel = []  # Diccionario con el/los nombre de los hoteles
        dic_hotel.append({'ID_Hotel': compan.id_hotel,
                          'Descripcion': compan.property_name.encode(
                              'ascii', 'xmlcharrefreplace')})

        dic_pais = []
        # Diccionario con los nombre de los Paises usando los del INE
        paises = self.env['code_ine'].search_read([], ['code', 'name'])
        for pais in paises:
            dic_pais.append({'ID_Hotel': compan.id_hotel,
                             'ID_Pais': pais['code'],
                             'Descripcion': pais['name'].encode(
                                 'ascii', 'xmlcharrefreplace')})

        dic_regimen = []  # TODO Diccionario con los diccRegimen
        dic_regimen.append({'ID_Hotel': compan.id_hotel,
                            'ID_Regimen': 0,
                            'Descripcion': u'Sin régimen'.encode(
                                'ascii', 'xmlcharrefreplace')})

        dic_estados = []  # Diccionario con los Estados Reserva
        estado_array = ['draft', 'confirm', 'booking', 'done', 'cancelled']
        for i in range(0, len(estado_array)):
            dic_estados.append({'ID_Hotel': compan.id_hotel,
                                'ID_EstadoReserva': i,
                                'Descripcion': estado_array[i]})

        dic_tipo_habitacion = []  # Diccionario con Virtuals Rooms
        tipo = self.env['hotel.virtual.room'].search_read(
            [], ['virtual_code', 'product_id'])
        for i in tipo:
            dic_tipo_habitacion.append({
                'ID_Hotel': compan.id_hotel,
                'ID_Tipo_Habitacion': i['product_id'][0],
                'Descripcion': i['product_id'][1].encode(
                    'ascii', 'xmlcharrefreplace')})

        dic_capacidad = []  # Diccionario con las capacidades
        for i in tipo:
            room = self.env['hotel.virtual.room'].search([
                ('product_id', '=', i['product_id'][0])])
            dic_capacidad.append({
                'ID_Hotel': compan.id_hotel,
                'Hasta_Fecha':
                (date.today() + timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
                'ID_Tipo_Habitacion': i['product_id'][0],
                'Nro_Habitaciones': len(room.room_ids)})

# Budget
# ID_Hotel numérico Código del Hotel
# Fecha fecha Primer día del mes
# ID_Tarifa numérico Código de la Tarifa
# ID_Canal numérico Código del Canal
# ID_Pais numérico Código del País
# ID_Regimen numérico Cóigo del Régimen
# ID_Tipo_Habitacion numérico Código del Tipo de Habitación
# iD_Segmento numérico Código del Segmento
# ID_Cliente numérico Código del Cliente
# Room_Nights numérico con dos decimales Número de Room Nights
# Room_Revenue numérico con dos decimales Ingresos por Reservas
# Pension_Revenue numérico con dos decimales Ingresos por Pensión
# Estancias numérico Número de Estancias
        budgets = self.env['data_bi'].search([])
        dic_budget = []  # Diccionario con las previsiones Budget
        for budget in budgets:
            dic_budget.append({'ID_Hotel': compan.id_hotel,
                               'Fecha': str(budget.year) + '-' +
                               str(budget.month).zfill(2) + '-01',
                               # 'ID_Tarifa': 0,
                               # 'ID_Canal': 0,
                               # 'ID_Pais': 0,
                               # 'ID_Regimen': 0,
                               # 'ID_Tipo_Habitacion': 0,
                               # 'ID_Cliente': 0,
                               'Room_Nights': budget.room_nights,
                               'Room_Revenue': budget.room_revenue,
                               # 'Pension_Revenue': 0,
                               'Estancias': budget.estancias})

        dic_moti_bloq = []  # Diccionario con Motivo de Bloqueos
        bloqeo_array = ['Staff', _('Out of Service')]
        for i in range(0, len(bloqeo_array)):
            dic_moti_bloq.append({'ID_Hotel': compan.id_hotel,
                                  'ID_Motivo_Bloqueo': i,
                                  'Descripcion': bloqeo_array[i].encode(
                                      'ascii', 'xmlcharrefreplace')})

        dic_bloqueos = []  # Diccionario con Bloqueos
        lineas = self.env['hotel.reservation.line'].search(
            ['&', ('date', '>=', fechafoto),
             ('reservation_id.reservation_type', '<>', 'normal'),
             ], order="date")
        for linea in lineas:
            if linea.reservation_id.reservation_type == 'out':
                id_m_b = 1
            else:
                id_m_b = 0
            dic_bloqueos.append({
                'ID_Hotel': compan.id_hotel,
                'Fecha_desde': linea.date,
                'Fecha_hasta': (datetime.strptime(linea.date, "%Y-%m-%d") +
                                timedelta(days=1)).strftime("%Y-%m-%d"),
                'ID_Tipo_Habitacion':
                linea.reservation_id.virtual_room_id.product_id.id,
                'ID_Motivo_Bloqueo': id_m_b,
                'Nro_Habitaciones': 1})

        lineas = self.env['res.partner.category'].search([])
        dic_segmentos = []  # Diccionario con Segmentación
        for linea in lineas:
            if linea.parent_id.name:
                seg_desc = linea.parent_id.name + " / " + linea.name
                dic_segmentos.append({'ID_Hotel': compan.id_hotel,
                                      'ID_Segmento': linea.id,
                                      'Descripcion': seg_desc.encode(
                                          'ascii', 'xmlcharrefreplace')})

        lineas = self.env['wubook.channel.info'].search([])
        dic_clientes = []  # Diccionario con Clientes (OTAs)
        dic_clientes.append({'ID_Hotel': compan.id_hotel,
                             'ID_Cliente': u'0',
                             'Descripcion': 'Ninguno'})
        for linea in lineas:
            dic_clientes.append({'ID_Hotel': compan.id_hotel,
                                 'ID_Cliente': linea.wid,
                                 'Descripcion': linea.name})
# ID_Reserva numérico Código único de la reserva
# ID_Hotel numérico Código del Hotel
# ID_EstadoReserva numérico Código del estado de la reserva
# FechaVenta fecha Fecha de la venta de la reserva
# ID_Segmento numérico Código del Segmento de la reserva
# ID_Cliente Numérico Código del Cliente de la reserva
# ID_Canal numérico Código del Canal
# FechaExtraccion fecha Fecha de la extracción de los datos (Foto)
# Entrada fecha Fecha de entrada
# Salida fecha Fecha de salida
# Noches numérico Nro. de noches de la reserva
# ID_TipoHabitacion numérico Código del Tipo de Habitación
# ID_Regimen numérico Código del Tipo de Régimen
# Adultos numérico Nro. de adultos
# Menores numérico Nro. de menores
# Cunas numérico Nro. de cunas
# PrecioDiario numérico con dos decimales Precio por noche de la reserva
# ID_Tarifa numérico Código de la tarifa aplicada a la reserva
# ID_Pais numérico Código del país
        dic_reservas = []
        # Diccionario con las Reservas
        lineas = self.env['hotel.reservation.line'].search(
            ['&', ('date', '>=', fechafoto),
             ('reservation_id.reservation_type', '=', 'normal'),
             ], order="date")
        for linea in lineas:
            id_estado_r = linea.reservation_id.state

            id_codeine = 0
            if linea.reservation_id.partner_id.code_ine.code:
                id_codeine = linea.reservation_id.partner_id.code_ine.code

            id_segmen = 0
            if len(linea.reservation_id.segmentation_id) > 0:
                id_segmen = linea.reservation_id.segmentation_id[0].id
            elif len(linea.reservation_id.partner_id.category_id) > 0:
                id_segmen = linea.reservation_id.partner_id.category_id[0].id

            chanel_r = 0
            if linea.reservation_id.channel_type:
                chanel_r = canal_array.index(linea.reservation_id.channel_type)

            precio_dto = 0
            if linea.reservation_id.discount != 0:
                precio_dto = linea.price * linea.reservation_id.discount/100

            channel_c = 0
            precio_comision = 0
            precio_neto = linea.price
            if linea.reservation_id.wrid:
                if linea.reservation_id.wchannel_id.wid:
                    channel_c = int(linea.reservation_id.wchannel_id.wid)
                    if channel_c == 1:
                        # Expedia.
                        precio_iva = (precio_neto*10/100)
                        precio_neto -= precio_iva
                        precio_comision = (precio_neto*18/100)
                        precio_neto -= precio_comision
                    elif channel_c == 2:
                        # Booking.
                        precio_comision = (precio_neto*15/100)
                        precio_neto -= precio_comision
                        precio_iva = (precio_neto*10/100)
                        precio_neto -= precio_iva
                    elif channel_c == 9:
                        # Hotelbeds
                        precio_comision = (precio_neto*20/100)
                        precio_neto -= precio_comision
                        precio_iva = (precio_neto*10/100)
                        precio_neto -= precio_iva
                    elif channel_c == 11:
                        # HRS
                        precio_comision = (precio_neto*20/100)
                        precio_neto -= precio_comision
                        precio_iva = (precio_neto*10/100)
                        precio_neto -= precio_iva
                else:
                    # Direct From Wubook (Web)
                    channel_c = 999
                    precio_iva = (precio_neto*10/100)
                    precio_neto -= precio_iva
            else:
                precio_iva = (precio_neto*10/100)
                precio_neto -= precio_iva
            dic_reservas.append({
                'ID_Reserva': linea.reservation_id.folio_id.id,
                'ID_Hotel': compan.id_hotel,
                'ID_EstadoReserva': estado_array.index(id_estado_r),
                'FechaVenta': linea.reservation_id.create_date[0:10],
                'ID_Segmento': id_segmen,
                'ID_Cliente': channel_c,
                'ID_Canal': chanel_r,
                'FechaExtraccion': date.today().strftime('%Y-%m-%d'),
                'Entrada': linea.date,
                'Salida': (datetime.strptime(linea.date, "%Y-%m-%d") +
                           timedelta(days=1)).strftime("%Y-%m-%d"),
                'Noches': 1,
                'ID_TipoHabitacion':
                linea.reservation_id.virtual_room_id.product_id.id,
                'ID_HabitacionDuerme': linea.reservation_id.product_id.id,
                'ID_Regimen': 0,
                'Adultos': linea.reservation_id.adults,
                'Menores': linea.reservation_id.children,
                'Cunas': 0,
                'PrecioDiario': precio_neto,
                'PrecioComision': precio_comision,
                'PrecioIva': precio_iva,
                'PrecioDto': precio_dto,
                'ID_Tarifa': linea.reservation_id.pricelist_id.id,
                'ID_Pais': id_codeine})

        dic_export = []  # Diccionario con todo lo necesario para exportar.
        if (archivo == 0) or (archivo == 1):
            dic_export.append({'Tarifa': dic_tarifa})
        if (archivo == 0) or (archivo == 2):
            dic_export.append({'Canal': dic_canal})
        if (archivo == 0) or (archivo == 3):
            dic_export.append({'Hotel': dic_hotel})
        if (archivo == 0) or (archivo == 4):
            dic_export.append({'Pais': dic_pais})
        if (archivo == 0) or (archivo == 5):
            dic_export.append({'Regimen': dic_regimen})
        if (archivo == 0) or (archivo == 6):
            dic_export.append({'Reservas': dic_reservas})
        if (archivo == 0) or (archivo == 7):
            dic_export.append({'Capacidad': dic_capacidad})
        if (archivo == 0) or (archivo == 8):
            dic_export.append({'Tipo Habitación': dic_tipo_habitacion})
        if (archivo == 0) or (archivo == 9):
            dic_export.append({'Budget': dic_budget})
        if (archivo == 0) or (archivo == 10):
            dic_export.append({'Bloqueos': dic_bloqueos})
        if (archivo == 0) or (archivo == 11):
            dic_export.append({'Motivo Bloqueo': dic_moti_bloq})
        if (archivo == 0) or (archivo == 12):
            dic_export.append({'Segmentos': dic_segmentos})
        if (archivo == 0) or (archivo == 13):
            dic_export.append({'Clientes': dic_clientes})
        if (archivo == 0) or (archivo == 14):
            dic_export.append({'Estado Reservas': dic_estados})

        dictionaryToJson = json.dumps(dic_export)
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        return dictionaryToJson

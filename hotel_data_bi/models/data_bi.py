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
from openerp.exceptions import except_orm, ValidationError
from odoo.addons.hotel import date_utils
from datetime import date, datetime, timedelta


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
    Room_Nights = fields.Float("Room Nights", required=True, digits=(6, 2))
    # Número de Room Nights
    Room_Revenue = fields.Float("Room Revenue", required=True, digits=(6, 2))
    # Ingresos por Reservas
    Estancias = fields.Integer("Number of Stays")  # Número de Estancias
    # ID_Tarifa numérico Código de la Tarifa
    # ID_Canal numérico Código del Canal
    # ID_Pais numérico Código del País
    # ID_Regimen numérico Cóigo del Régimen
    # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
    # iD_Segmento numérico Código del Segmento
    # ID_Cliente numérico Código del Cliente
    # Pension_Revenue numérico con dos decimales Ingresos por Pensión

    @api.multi
    def export(self, lugar, fechafoto=date.today()):
        """Management and export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        """
        self.ensure_one()
        compan = self.env.user.company_id

        diccTarifa = []  # Diccionario con las tarifas
        tarifas = self.env['product.pricelist'].search_read([], ['name'])
        for tarifa in tarifas:
            diccTarifa.append({'ID_Hotel': compan.id_hotel,
                               'ID_Tarifa': tarifa['id'],
                               'Descripcion': tarifa['name']})

        diccCanal = []  # TODO Diccionario con los Canales
        diccCanal.append({'ID_Hotel': compan.id_hotel,
                          'ID_Canal': 'xxxxx',
                          'Descripcion': 'xxxxx'})

        diccHotel = []  # Diccionario con el/los nombre de los hoteles
        diccHotel.append({'ID_Hotel': compan.id_hotel,
                          'Descripcion': compan.property_name})

        diccPais = []
        # Diccionario con los nombre de los Paises usando los del INE
        paises = self.env['code_ine'].search_read([], ['code', 'name'])
        for pais in paises:
            diccPais.append({'ID_Hotel': compan.id_hotel,
                             'ID_Pais': pais['code'],
                             'Descripcion': pais['name']})

        diccRegimen = []  # TODO Diccionario con los diccRegimen
        diccRegimen.append({'ID_Hotel': compan.id_hotel,
                            'ID_Regimen': 'xxxxx',
                            'Descripcion': 'xxxxx',})

        diccEstados = []  # Diccionario con los Estados Reserva
        estado_array = ['draft', 'confirm', 'booking', 'done', 'cancelled']
        for i in range(0, len(estado_array)):
            diccEstados.append({'ID_Hotel': compan.id_hotel,
                                'ID_EstadoReserva': i,
                                'Descripcion': estado_array[i]})

        diccTipo_Habitacion = []  # Diccionario con Virtuals Rooms
        tipo = self.env['hotel.virtual.room'].search_read(
            [], ['virtual_code', 'product_id'])
        for i in tipo:
            diccTipo_Habitacion.append({
                'ID_Hotel': compan.id_hotel,
                'ID_Tipo_Habitacion': i['product_id'][0],
                'Descripcion': i['product_id'][1]})

        diccCapacidad = []  # TODO Diccionario con las capacidades
        diccCapacidad.append({'ID_Hotel': compan.id_hotel,
                              'Hasta_Fecha': 'xxxxx',
                              'ID_Tipo_Habitacion': 'xxxxx',
                              'Nro_Habitaciones': 'xxxxx'})

        budgets = self.env['data_bi'].search([])
        diccBudget = []  # Diccionario con las previsiones Budget
        for budget in budgets:
            diccBudget.append({'ID_Hotel': compan.id_hotel,
                               'Fecha': str(budget.year) + '-'
                               + str(budget.month).zfill(2) + '-01',
                               # 'ID_Tarifa': 0,
                               # 'ID_Canal': 0,
                               # 'ID_Pais': 0,
                               # 'ID_Regimen': 0,
                               # 'ID_Tipo_Habitacion': 0,
                               # 'ID_Cliente': 0,
                               'Room_Nights': budget.Room_Nights,
                               'Room_Revenue': budget.Room_Revenue,
                               # 'Pension_Revenue': 0,
                               'Estancias': budget.Estancias})
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

        diccMotivBloq = []  # Diccionario con Motivo de Bloqueos
        bloqeo_array = ['Staff', _('Out of Service')]
        for i in range(0, len(bloqeo_array)):
            diccMotivBloq.append({'ID_Hotel': compan.id_hotel,
                                  'ID_Motivo_Bloqueo': i,
                                  'Descripción': bloqeo_array[i]})
# Motivo Bloqueos
# ID_Hotel numérico Código del Hotel
# ID_Motivo_Bloqueo numérico Código del motivo del bloqueo de la habitacion
# Descripción texto(50) Descripción del tipo de habitación

        diccBloqueos = []  # Diccionario con Bloqueos
        lineas = self.env['hotel.reservation.line'].search(
            ['&', ('date', '>=', fechafoto),
             ('reservation_id.reservation_type', '<>', 'normal'),
             ], order="date")
        for linea in lineas:
            if linea.reservation_id.reservation_type == 'out':
                id_m_b = 1
            else:
                id_m_b = 0
            diccBloqueos.append({
                'ID_Hotel': compan.id_hotel,
                'Fecha_desde': linea.date,
                'Fecha_hasta': (datetime.strptime(linea.date, "%Y-%m-%d") +
                                timedelta(days=1)).strftime("%Y-%m-%d"),
                'ID_Tipo_Habitacion':
                linea.reservation_id.virtual_room_id.product_id.id,
                'ID_Motivo_Bloqueo': id_m_b,
                'Nro_Habitaciones': 1,
                })
# Bloqueos
# ID_Hotel numérico Código del Hotel
# Fecha_desde fecha Fecha de inicio de bloqueo
# Fecha_hasta fecha Fecha de final de bloqueo
# ID_Tipo_Habitacion numérico Código del Tipo de Habitacion
# ID_Motivo_Bloqueo numérico Código del Motivo del Bloqueo
# Nro_Habitaciones numérico con dos decimales Número de habitaciones bloqueadas

        diccSegmentos = []  # TODO Diccionario con Segmentos
        diccSegmentos.append({'ID_Hotel': compan.id_hotel,
                              'ID_Segmento': 'xxxxx',
                              'Descripción': 'xxxxx'})
# Segmentos
# ID_Hotel numérico Código del Hotel
# ID_Segmento numérico Código del segmento de la reserva
# Descripción texto(50) Descripción del tipo de habitación

        diccClientes = []  # TODO Diccionario con Clientes
        diccClientes.append({'ID_Hotel': compan.id_hotel,
                             'ID_Cliente': 'xxxxx',
                             'Descripción': 'xxxxx'})
# Clientes
# ID_Hotel numérico Código del Hotel
# ID_Cliente numérico Código del Cliente de la reserva
# Descripción texto(50) Descripción del Cliente



        diccReservas = []
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
            diccReservas.append({
                'ID_Reserva': linea.reservation_id.folio_id.id,
                'ID_Hotel': compan.id_hotel,
                'ID_EstadoReserva': estado_array.index(id_estado_r),
                'FechaVenta': linea.reservation_id.create_date[0:10],
                'ID_Segmento': 'xxxxx',
                'ID_Cliente': 'xxxxx',
                'ID_Canal': 'xxxxx',
                'FechaExtraccion': date.today().strftime('%Y-%m-%d'),
                'Entrada': linea.date,
                'Salida': (datetime.strptime(linea.date, "%Y-%m-%d") +
                           timedelta(days=1)).strftime("%Y-%m-%d"),
                'Noches': 1,
                'ID_TipoHabitacion':
                linea.reservation_id.virtual_room_id.product_id.id,
                'ID_Regimen': 'xxxxx',
                'Adultos': linea.reservation_id.adults,
                'Menores': linea.reservation_id.children,
                'Cunas': 0,
                'PrecioDiario': linea.price,
                'ID_Tarifa': linea.reservation_id.pricelist_id,
                'ID_Pais': id_codeine})

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


        # Debug Stop -------------------
        import wdb; wdb.set_trace()
        # Debug Stop -------------------
        return diccTarifa

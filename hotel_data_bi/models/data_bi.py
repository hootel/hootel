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
from datetime import datetime, date, time, timedelta


class Data_Bi(models.Model):

    """Management and export data for MopSolution MyDataBI."""
    _name = 'data_bi'

    Fecha = fields.Date("Primer dia mes")  # fecha Primer día del mes
    Room_Nights = fields.Float("Room Nights", digits=(6, 2))
    # Número de Room Nights
    Room_Revenue = fields.Float("Room Nights", digits=(6, 2))
    # Ingresos por Reservas
    Estancias = fields.Integer()  # Número de Estancias

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
                          'ID_Canal': tarifa['id'],
                          'Descripcion': tarifa['name']})

        diccHotel = []  # Diccionario con los nombre de los hoteles
        diccHotel.append({'ID_Hotel': compan.id_hotel,
                          'Descripcion': compan.property_name})

        diccPais = []
        # Diccionario con los nombre de los Paises TODO ¿necesidad de esto?
        paises = self.env['code_ine'].search_read([], ['name'])
        for pais in paises:
            diccPais.append({'ID_Hotel': compan.id_hotel,
                             'ID_Pais': pais['id'],
                             'Descripcion': pais['name']})

        diccRegimen = []  # TODO Diccionario con los diccRegimen
        diccRegimen.append({'ID_Hotel': compan.id_hotel,
                            'ID_Regimen': tarifa['id'],
                            'Descripcion': tarifa['name']})

        diccReservas = []
        # Diccionario con los nombre de los Paises TODO ¿necesidad de esto?
        lineas = self.env['hotel.reservation.line'].search(
            ['&', ('date', '>=', fechafoto),
             ('reservation_id.reservation_type', '=', 'normal'),
             ], order="date")
        for linea in lineas:
            diccReservas.append({'ID_Reserva': 'xxxxx',
                                 'ID_Hotel': compan.id_hotel,
                                 'ID_EstadoReserva': 'xxxxx',
                                 'FechaVenta': 'xxxxx',
                                 'ID_Segmento': 'xxxxx',
                                 'ID_Cliente': 'xxxxx',
                                 'ID_Canal': 'xxxxx',
                                 'FechaExtraccion': 'xxxxx',
                                 'Entrada': 'xxxxx',
                                 'Salida': 'xxxxx',
                                 'Noches': 'xxxxx',
                                 'ID_TipoHabitacion': 'xxxxx',
                                 'ID_Regimen': 'xxxxx',
                                 'Adultos': 'xxxxx',
                                 'Menores': 'xxxxx',
                                 'Cunas': 'xxxxx',
                                 'PrecioDiario': linea.price,
                                 'ID_Tarifa': 'xxxxx',
                                 'ID_Reserva': 'xxxxx',
                                 'ID_Reserva': 'xxxxx',
                                 'ID_Reserva': 'xxxxx',
                                 'ID_Pais': pais['id']})

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
# PrecioDiario
# numérico con
# dos decimales Precio por noche de la reserva
# ID_Tarifa numérico Código de la tarifa aplicada a la reserva
# ID_Pais numérico Código del país


        # Debug Stop -------------------
        import wdb; wdb.set_trace()
        # Debug Stop -------------------
        return diccTarifa

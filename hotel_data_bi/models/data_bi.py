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
    def export(self, fechafoto=date.today()):
        self.ensure_one()
        compan = self.env.user.company_id
        diccTarifa = []  # Diccionario con las tarifas
        tarifas = self.env['product.pricelist'].search_read([], ['name'])
        for tarifa in tarifas:
            diccTarifa.append({'ID_Hotel': compan.ID_Hotel,
                               'ID_Tarifa': tarifa['id'],
                               'Descripcion': tarifa['name']})

        diccCanal = []  # TODO Diccionario con los Canales
        diccCanal.append({'ID_Hotel': compan.ID_Hotel,
                          'ID_Canal': tarifa['id'],
                          'Descripcion': tarifa['name']})

        diccHotel = []  # Diccionario con los nombre de los hoteles
        diccHotel.append({'ID_Hotel': compan.ID_Hotel,
                          'Descripcion': compan.property_name})

        diccPais = []
        paises = self.env['code_ine'].search_read([], ['name'])
        for pais in paises:
            # Diccionario con los nombre de los Paises TODO ¿necesidad de esto?
            diccPais.append({'ID_Hotel': compan.ID_Hotel,
                             'ID_Pais': pais['id'],
                             'Descripcion': pais['name']})

        diccRegimen = []  # TODO Diccionario con los diccRegimen
        diccRegimen.append({'ID_Hotel': compan.ID_Hotel,
                            'ID_Regimen': tarifa['id'],
                            'Descripcion': tarifa['name']})

        # Debug Stop -------------------
        import wdb; wdb.set_trace()
        # Debug Stop -------------------
        return diccTarifa

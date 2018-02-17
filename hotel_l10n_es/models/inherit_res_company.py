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
from openerp import models, fields, api


class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    property_name = fields.Char('Property name',
                                help='Name of the Hotel/Property.')
    tourism = fields.Char('Tourism number',
                          help='Registration number in the Ministry of \
                                            Tourism. Used for INE statistics.')
    rooms = fields.Integer('Rooms Available', default=0,
                           help='Used for INE statistics.')
    seats = fields.Integer('Beds available', default=0,
                           help='Used for INE statistics.')
    permanentstaff = fields.Integer('Permanent Staff', default=0,
                                    help='Used for INE statistics.')
    eventualstaff = fields.Integer('Eventual Staff', default=0,
                                   help='Used for INE statistics.')
    police = fields.Char('Police number', size=10,
                         help='Used to generate the name of the file that \
                                    will be given to the police. 10 Caracters')
    category_id = fields.Many2one('category',
                                  help='Hotel category in the Ministry of \
                                            Tourism. Used for INE statistics.')
    cardex_warning = fields.Text(
        'Warning in Cardex',
        default="Hora de acceso a habitaciones: 14:00h. Hora de salida: \
                    12:00h. Si no se abandona el alojamiento a dicha hora, \
                    el establecimiento cobrará un día de estancia según \
                    tarifa vigente ese día.",
        help="Notice under the signature on the traveler's ticket.")
    # hotel_latitude = fields.Char('Latitude', default="40.964971",
    #             help="Provide latitude for google maps in mail template.\
    #                 Example 40.964971 or -5.6641045\
    #                 It points to the main square of Salamanca.")
    # hotel_longitude = fields.Char('Longitude', default="-5.6641045",
    #             help="Provide longitude for google maps in mail template.\
    #                 Example 40.964971 or -5.6641045\
    #                 It points to the main square of Salamanca.")

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
import logging
_logger=logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Validation for under age clients (16 years old)
    #~ @api.constrains('birthdate_date')
    #~ def validation_under_age(self):
        #~ from datetime import datetime, timedelta

        #~ years = str(datetime.now().date() - timedelta(days=365*16+4))
        #~ limit_date = datetime.strptime(years, "%Y-%m-%d")
        #~ birth_date = datetime.strptime(self.birthdate_date, '%Y-%m-%d')
        #~ if limit_date < birth_date:
            #~ raise models.ValidationError(
                #~ 'The client is under 16 years old. Data collection is not performed for those born before %s.' % (years))


    #~ # Validation for expedicion anterior al nacimiento
    #~ @api.constrains('polexpedition')
    #~ def validation_expedition_under_birth(self):
        #~ if self.birthdate_date > self.polexpedition:
            #~ raise models.ValidationError('Date of document shipment, prior to birth date')

    # Validation for Tipo de documento no valido para Extranjero
    # @api.constrains('x')
    # Pendiente


    # Validation for Nacionalidad erronea
    # @api.constrains('x')
    # Pendiente

    # Validation for DNI/Permiso conducir erroneo
    #~ @api.constrains('documenttype')
    #~ def validation_poldocument_type(self):
        #~ _logger.info('---TTTTTTTTTTTTTT----')
        #~ _logger.info(self.documenttype)
        #~ if self.documenttype in ['D','C','I']:
            #~ _logger.info(self.poldocument)

    # Validation for DNI/Permiso conducir erroneo
    #~ @api.constrains('poldocument')
    #~ def validation_poldocument_dni(self):
        #~ _logger.info('----------')
        #~ _logger.info(self.documenttype)
        #~ if self.documenttype in ['D','C','I']:
            #~ validcaracter = "TRWAGMYFPDXBNJZSQVHLCKE"
            #~ dig_ext = "XYZ"
            #~ reemp_dig_ext = {'X':'0', 'Y':'1', 'Z':'2'}
            #~ numeros = "1234567890"
            #~ dni = self.poldocument.upper()
            #~ _logger.info(dni)
            #~ if len(dni) == 9:
                #~ dig_control = dni[8]
                #~ dni = dni[:8]
                #~ _logger.info('Control es')
                #~ _logger.info(dig_control)
                #~ if dni[0] in dig_ext:
                    #~ _logger.info('extranjero empieza por XYZ')
                    #~ dni = dni.replace(dni[0], reemp_dig_ext[dni[0]])
                    #~ _logger.info(dni)
                #~ if (len(dni) == len([n for n in dni if n in numeros])) and (validcaracter[int(dni)%23] == dig_control):
                    #~ _logger.info('Esta O.K.')
                #~ else:
                    #~ raise models.ValidationError('DNI/NIE erroneo reviselo')
            #~ else:
                #~ raise models.ValidationError('DNI/NIE longitud erronea formato correcto: (12345678A o X1234567A)')
        #~ _logger.info('----------')

    # Validation for Fecha anterior a 1900
    # @api.constrains('x')
    # Pendiente


    # Validation for Fecha posterior a hoy
    # @api.constrains('x')
    # Pendiente


    # Validation for unicos caracteres permitos numeros y letras
    # @api.constrains('x')
    # Pendiente
    documenttype = fields.Selection([
        ('D', 'DNI'),
        ('P', 'Pasaporte'),
        ('C', 'Permiso de Conducir'),
        ('I', 'Carta o Doc. de Identidad'),
        ('N', 'Permiso Residencia Español'),
        ('X', 'Permiso Residencia Europeo')],
        help='blabla',
        string='Document type')
    poldocument = fields.Char('Document number')
    polexpedition = fields.Date('Document expedition date')
    birthdate_date = fields.Date("Birthdate")
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female')])
    code_ine = fields.Many2one('code_ine',
            help='Country or province of origin. Used for INE statistics.')

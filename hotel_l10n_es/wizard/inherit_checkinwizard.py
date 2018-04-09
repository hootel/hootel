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

from openerp import models, fields, api
from openerp.exceptions import UserError
from openerp.tools.translate import _
import logging
from datetime import datetime, timedelta
_logger=logging.getLogger(__name__)

class Wizard(models.TransientModel):
    _inherit = 'checkin.wizard'

    # Birthdate validation
    @api.onchange('birthdate_date_cardex')
    def validation_under_age(self):
        if self.birthdate_date_cardex <> False:
            years = str(datetime.now().date() - timedelta(days=365*16+4))
            limit_date = datetime.strptime(years, "%Y-%m-%d")
            birth_date = datetime.strptime(self.birthdate_date_cardex, '%Y-%m-%d')
            limite = str(limit_date.day)+ ' de ' +  str(limit_date.month)+ ' de ' + str(limit_date.year)
            if limit_date < birth_date:
                return {'warning': {'title': _('Error in Birthdate'), 'message': _('Does the client have less than 16 years?. Data collection is not performed for those born before %s.' % (limite)),},}
            if self.polexpedition_cardex <> False:
                if self.birthdate_date_cardex > self.polexpedition_cardex:
                    return {'warning': {'title': _('Error in Birthdate or Expedition date'), 'message': _('Date of document shipment, prior to birth date'),},}

    # Expedition validation
    @api.onchange('polexpedition_cardex')
    def validation_polexpedition(self):
        if self.birthdate_date_cardex <> False and self.polexpedition_cardex <> False:
            if self.birthdate_date_cardex > self.polexpedition_cardex:
                return {'warning': {'title': _('Error in Birthdate or Expedition date'), 'message': _('Date of document shipment, prior to birth date'),},}

    # Validation for DNI/Permiso conducir erroneo
    @api.onchange('poldocument_cardex', 'documenttype_cardex')
    def validation_poldocument_dni(self):
        if self.poldocument_cardex <> False:
            if self.documenttype_cardex in ['D','C','I']:
                validcaracter = "TRWAGMYFPDXBNJZSQVHLCKE"
                dig_ext = "XYZ"
                reemp_dig_ext = {'X':'0', 'Y':'1', 'Z':'2'}
                numeros = "1234567890"
                dni = self.poldocument_cardex.upper()
                if len(dni) == 9:
                    dig_control = dni[8]
                    dni = dni[:8]
                    # 'extranjero empieza por XYZ'
                    if dni[0] in dig_ext:
                        dni = dni.replace(dni[0], reemp_dig_ext[dni[0]])
                    if not ((len(dni) == len([n for n in dni if n in numeros])) and (validcaracter[int(dni)%23] == dig_control)):
                        return {'warning': {'title': _('Error in DNI/NIE/DRIVE LICENSE'), 'message': _('Wrong DNI/NIE/DRIVE LICENSE, check it.'),},}
                else:
                    return {'warning': {'title': _('Error in DNI/NIE/DRIVE LICENSE'), 'message': _('DNI/NIE/DRIVE LICENSE erroneous length, the correct format is: (12345678A or X1234567A)'),},}

    # Validation for Tipo de documento no valido para Extranjero
    # @api.onchange('x')
    # Pendiente

    # Validation for Nacionalidad erronea
    # @api.onchange('x')
    # Pendiente

    documenttype_cardex = fields.Selection([
        ('D', 'DNI'),
        ('P', 'Pasaporte'),
        ('C', 'Permiso de Conducir'),
        ('I', 'Carta o Doc. de Identidad'),
        ('N', 'Permiso Residencia Español'),
        ('X', 'Permiso Residencia Europeo')],
        help=_('Select a valid document type'),
        required=True,
        default='D',
        string=_('Doc. type'),
        related='partner_id.documenttype')
    poldocument_cardex = fields.Char('Doc. number', required=True, related='partner_id.poldocument')
    polexpedition_cardex = fields.Date('Expedition date', required=True, related='partner_id.polexpedition')
    birthdate_date_cardex = fields.Date("Birthdate", required=True, related='partner_id.birthdate_date')
    gender_cardex = fields.Selection([('male', 'Male'),
                               ('female', 'Female')],
                                required=True, related='partner_id.gender')
    firstname_cardex = fields.Char('Firstname', required=True, related='partner_id.firstname')
    lastname_cardex = fields.Char('Lastname', required=True, related='partner_id.lastname')
    mobile_cardex = fields.Char('Mobile', related='partner_id.mobile', store=True)
    code_ine_cardex = fields.Many2one('code_ine',
            help=_('Country or province of origin. Used for INE statistics.'),
            required=True,
            related='partner_id.code_ine')
    category_id_cardex = fields.Many2many('res.partner.category', 'id', related='partner_id.category_id', required=True)

    @api.multi
    def pdf_viajero(self, cardex_id):
        cardex = self.env['cardex'].search([('id', '=', cardex_id)])
#         data['cardex'] = cardex_id
#         datas = {
#              'ids': cardex_ids,
#              'model': 'cardex',
#              'form': data
#         }
        return self.env['report'].get_action(cardex, 'report.viajero')

    @api.multi
    def action_save_check(self):
        cardex_val = {
            'partner_id': self.partner_id.id,
            'enter_date': self.enter_date,
            'exit_date': self.exit_date,
        }
        record_id = self.env['hotel.reservation'].browse(self.reservation_id.id)
        old_cardex = self.env['cardex'].search([('reservation_id', '=', record_id.id)])
        record_id.write({
            'cardex_ids': [(0, False, cardex_val)]
        })
        if record_id.cardex_count > 0:
            record_id.state = 'booking'
            record_id.is_checkin = False
            folio = self.env['hotel.folio'].browse(self.reservation_id.folio_id.id)
            folio.checkins_reservations -= 1
        cardex = self.env['cardex'].search([('reservation_id', '=', record_id.id)]) - old_cardex
        # now_cardex = self.env['cardex'].search([("reservation_id","=",record_id.id),
        #     ("partner_id","=",self.partner_id.id),
        #     ("enter_date","=",self.enter_date),
        #     ("exit_date","=",self.exit_date),
        #     ],limit=1)

        #context = { 'ids': now_cardex.id,
            # 'partner_id': record_id.partner_id,
            # 'enter_date': record_id.cardex_ids.enter_date,
            # 'exit_date': record_id.cardex_ids.exit_date,
            # 'reserva_id': record_id.cardex_ids.reservation_id,
            # 'hidden_cardex': True,
            # 'edit_cardex': True
        #    }
#         context = {
#             'partner_id': cardex.partner_id,
#             'enter_date': cardex.enter_date,
#             'exit_date': cardex.exit_date,
#             'reserva_id': cardex.id,
#             'hidden_cardex': True,
#             'edit_cardex': True
#         }
        # FIXME: Hackish solution for close & print (https://www.odoo.com/es_ES/forum/ayuda-1/question/close-wizard-after-print-report-86786)
        action_report = self.pdf_viajero(cardex.id)
        #del action_report['report_type']
        return action_report
        #return {'type': 'ir.actions.act_window_close'}


        # Debug Stop -------------------
        #    import wdb; wdb.set_trace()
        # Debug Stop -------------------

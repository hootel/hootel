# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
from datetime import datetime
import logging
# from odoo.addons.hotel_l10n_es.code_ine import CodeIne
from odoo.addons.hotel_roommatik.models.roommatik import (
    DEFAULT_ROOMMATIK_DATE_FORMAT)


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def fc_set_partner(self, customer):
        # FastCheckin API CREACIÓN DE CLIENTE
        _logger = logging.getLogger(__name__)
        ReservationId = customer['ReservationId']
        del customer['ReservationId']

        if customer['country_id'] == 'ESP':
            country_data = self.env['code.ine'].search(
                [('name', '=', customer['state_id'])])
            if len(country_data) > 1:
                customer['state_id'] = country_data[1].state_id.id
                customer['country_id'] = country_data[1].state_id.country_id.id
                customer['code_ine_id'] = country_data[1].id

            else:
                customer['state_id'] = country_data[0].state_id.id
                customer['country_id'] = country_data[0].state_id.country_id.id
                customer['code_ine_id'] = country_data[0].id

        else:
            country_data = self.env['code.ine'].search(
                [('code', 'ilike', customer['country_id'])])
            country_data2 = self.env['res.country'].search(
                         [('code_alpha3', '=', customer['country_id'])])
            customer['country_id'] = country_data2.id
            customer['street2'] = customer['state_id']
            customer['code_ine_id'] = country_data.id
            del customer['state_id']





        partner_res = self.env['res.partner'].search([(
            'document_number', '=',
            customer['document_number'])])

        json_response = {'Id': 0}
        write_customer = False
        if any(partner_res):
            # Change customer data
            try:
                partner_res[0].update(customer)
                write_customer = partner_res[0]
                _logger.info('FASTCHECKIN %s exist in BD [ %s ] Rewriting',
                             partner_res[0].document_number,
                             partner_res[0].id,)
            except Exception as e:
                if 'args' in e.__dir__():
                    error_name = e.args
                else:
                    error_name = e.name
        else:

            # Create new customer
            try:
                self.create(customer)
                _logger.info('FASTCHECKIN Created %s Name: %s',
                             customer['lastname'],
                             customer['firstname'])
                write_customer = self.env['res.partner'].search([
                     ('lastname', '=', customer['lastname'])])
            except Exception as e:
                if 'args' in e.__dir__():
                    error_name = e.args
                else:
                    error_name = e.name

                partner_res = self.env['res.partner'].search([(
                    'lastname', '=',
                    customer['lastname'])])
                partner_res.unlink()

        if write_customer:
            json_response = "OK"
            json_response = json.dumps(json_response)
            return json_response
        else:
            _logger.error(error_name)
            return [False, error_name]

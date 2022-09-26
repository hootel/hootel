# Copyright 2020 - 2022 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import models, fields, api
# from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fc_set_partner(self, customer):
        # FastCheckin API CREACIÓN DE CLIENTE
        _logger.info('FASTCHECKIN TO: %s ', customer)
        ReservationId = customer['ReservationId']
        del customer['ReservationId']

        nationality = self.env['res.country'].search(
            [('code', '=', customer['nationality_id'])])
        customer['nationality_id'] = nationality.id

        customer['country_id'] = self.env['res.country'].search(
            [('code', '=', customer['country_id'])])


        if customer['country_id'].code == 'ES':
            # habitual_residence
            zip = self.env['res.better.zip'].search(
                [('name', '=', customer['zip'])],
                limit=1)
            if not zip:
                zip = self.env['res.better.zip'].search(
                    [('name', '=', '28001')],
                    limit=1)
            customer['city'] = zip.city
            customer['country_id'] = zip.country_id.id
            customer['state_id'] = zip.state_id.id
            customer['zip'] = zip.name
            customer['zip_id'] = zip.id
            ine_code = self.env['code.ine'].search(
                [('name', 'ilike', zip.state_id.name)])
            if not ine_code:
                ine_code = self.env['code.ine'].search(
                    [('name', 'ilike', 'Madrid')])

            customer['code_ine_id'] = ine_code.id
        else:
            ine_code = self.env['code.ine'].search(
                [('code', '=', customer['country_id'].code_alpha3)])
            customer['code_ine_id'] = ine_code.id
            customer['country_id'] = customer['country_id'].id
            customer['city'] = False
            customer['state_id'] = False

        if 'kinship' in customer:
            kinship_data = customer['kinship']
            del customer['kinship']
        else:
            kinship_data = ''


        # if customer['country_id'] == 'ESP':
        #     country_data = self.env['code.ine'].search(
        #         [('name', 'ilike', customer['state_id'])])
        #     state_data = self.env['res.country.state'].search(
        #         [('name', 'ilike', customer['state_id'])])
        #     if len(country_data) > 1:
        #         customer['state_id'] = state_data[0].id
        #         customer['country_id'] = country_data[1].state_id.country_id.id
        #         customer['code_ine_id'] = country_data[1].id
        #
        #     elif len(country_data) == 1:
        #         customer['state_id'] = state_data[0].id
        #         customer['country_id'] = country_data[0].state_id.country_id.id
        #         customer['code_ine_id'] = country_data[0].id
        #     else:
        #         country_data = self.env['code.ine'].search(
        #             [('name', '=', 'Madrid')])
        #         state_data = self.env['res.country.state'].search(
        #             [('name', 'ilike', customer['Madrid'])])
        #         customer['state_id'] = state_data[0].id
        #         customer['country_id'] = country_data[0].state_id.country_id.id
        #         customer['code_ine_id'] = country_data[0].id
        #
        # else:
        #     country_data = self.env['code.ine'].search(
        #         [('code', 'ilike', customer['country_id'])])
        #     country_data2 = self.env['res.country'].search(
        #                  [('code_alpha3', '=', customer['country_id'])])
        #     customer['country_id'] = country_data2.id
        #     customer['street2'] = customer['state_id']
        #     customer['code_ine_id'] = country_data.id
        #     del customer['state_id']

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
                             partner_res[0].id, )
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
                    ('document_number', '=', customer['document_number'])])
            except Exception as e:
                if 'args' in e.__dir__():
                    error_name = e.args
                else:
                    error_name = e.name

                partner_res = self.env['res.partner'].search([(
                    'document_number', '=',
                    customer['document_number'])])
                partner_res.unlink()

        if write_customer:
            return self.fc_write_checkin(ReservationId, write_customer, kinship_data)

        else:
            _logger.error(error_name)
            error_name = str(error_name).replace("'", "*")
            json_response = json.dumps({'Error': error_name})
            return json_response

    def fc_write_checkin(self, ReservationId, partner_res, kinship_data):
        _logger.info('FASTCHECKIN checkin customer in %s Reservation.',
                     ReservationId)

        reservation_obj = self.env['hotel.reservation'].search([
            ('id', '=', ReservationId)])
        if reservation_obj.checkin_partner_pending_count > 0:

            checkin_partner_val = {
                'folio_id': reservation_obj.folio_id.id,
                'reservation_id': reservation_obj.id,
                'partner_id': partner_res.id,
                'enter_date': reservation_obj.checkin,
                'exit_date': reservation_obj.checkout,
                'code_ine_id': partner_res.code_ine_id.id,
                'kinship' : kinship_data
            }

            try:
                record = self.env['hotel.checkin.partner'].create(
                    checkin_partner_val)
                _logger.info('''FASTCHECKIN check-in partner: %s in
                              (%s Reservation) ID:%s.''',
                             checkin_partner_val['partner_id'],
                             checkin_partner_val['reservation_id'],
                             record.id)
                reservation_obj.folio_id.fc_counts += 1
            except Exception as e:
                error_name = 'Error not create Checkin '
                error_name += str(e)
                json_response = {'Error': error_name}
                _logger.error('FASTCHECKIN Error Checkin %s in reserv.: %s).',
                              checkin_partner_val['partner_id'],
                              checkin_partner_val['reservation_id'])
                json_response = json.dumps(json_response)
                return json_response
        else:
            _logger.error('FASTCHECKIN Nº chekcin exceded')
            json_response = {'Error': "Nº chekcin exceded"}
            json_response = json.dumps(json_response)
            return json_response

        json_response = "<strong>Fast-Checkin</strong></br> "
        json_response += "Creado a nombre de "
        json_response += "<strong>" + partner_res.name + '<strong>'

        reservation_obj.message_post(body=json_response,
                                     subject='Fast Checkin System')

        json_response = "OK"
        json_response = json.dumps(json_response)
        return json_response

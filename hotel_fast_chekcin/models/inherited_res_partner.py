# Copyright 2020 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
import logging


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

            elif len(country_data) == 1:
                customer['state_id'] = country_data[0].state_id.id
                customer['country_id'] = country_data[0].state_id.country_id.id
                customer['code_ine_id'] = country_data[0].id
            else:
                country_data = self.env['code.ine'].search(
                    [('name', '=', 'Madrid')])
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
            self.fc_write_checkin(ReservationId, partner_res)
            json_response = "OK"
            json_response = json.dumps(json_response)
            return json_response
        else:
            _logger.error(error_name)
            return [False, error_name]

    def fc_write_checkin(self, ReservationId, partner_res):
        _logger = logging.getLogger(__name__)
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
                }

            try:
                record = self.env['hotel.checkin.partner'].create(
                    checkin_partner_val)
                _logger.info('FASTCHECKIN check-in partner: %s in \
                                                (%s Reservation) ID:%s.',
                             checkin_partner_val['partner_id'],
                             checkin_partner_val['reservation_id'],
                             record.id)

                stay = {}
                stay['Id'] = record.id
                stay['Room'] = {}
                stay['Room']['Id'] = reservation_obj.room_id.id
                stay['Room']['Name'] = reservation_obj.room_id.name
                json_response = stay
            except Exception as e:
                error_name = 'Error not create Checkin '
                error_name += str(e)
                json_response = {'Error': error_name}
                _logger.error('FASTCHECKIN writing %s in reservation: %s).',
                              checkin_partner_val['partner_id'],
                              checkin_partner_val['reservation_id'])
                return json_response
        else:
            _logger.error('FASTCHECKIN Nº chekcin exceded')
            json_response = {'Error': "Nº chekcin exceded"}
            json_response = json.dumps(json_response)
            return json_response

        json_response = "<strong>Fast-Checkin</strong></br> "
        json_response += "Creado por la alicación.</br> A nombre de "
        json_response += "<strong>" + partner_res.name + '<strong>'

        reservation_obj.message_post(body=json_response)

        json_response = "OK"
        json_response = json.dumps(json_response)
        return json_response

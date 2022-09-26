# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
from datetime import datetime
import logging
from odoo.addons.hotel_roommatik.models.roommatik import (
    DEFAULT_ROOMMATIK_DATE_FORMAT)
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def rm_add_customer(self, customer):
        # RoomMatik API CREACIÓN DE CLIENTE
        _logger = logging.getLogger(__name__)

        partner_res = self.env['res.partner'].search([(
            'document_number', '=',
            customer['IdentityDocument']['Number'])])

        json_response = {'Id': 0}
        write_customer = False
        if any(partner_res):
            # Change customer data
            try:
                partner_res[0].update(self.rm_prepare_customer(customer))
                write_customer = partner_res[0]
                _logger.info('ROOMMATIK %s exist in BD [ %s ] Rewriting',
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
                self.create(self.rm_prepare_customer(customer))
                _logger.info('ROOMMATIK Created %s Name: %s',
                             customer['IdentityDocument']['Number'],
                             customer['FirstName'])
                write_customer = self.env['res.partner'].search([
                     ('document_number', '=',
                      customer['IdentityDocument']['Number'])])
            except Exception as e:
                if 'args' in e.__dir__():
                    error_name = e.args
                else:
                    error_name = e.name

                partner_res = self.env['res.partner'].search([(
                    'document_number', '=',
                    customer['IdentityDocument']['Number'])])
                partner_res.unlink()

        if write_customer:
            json_response = self.rm_get_a_customer(write_customer.id)
            json_response = json.dumps(json_response)
            return json_response
        else:
            _logger.error(error_name)
            return [False, error_name]

    def rm_prepare_customer(self, customer):
        _logger.info('-----------------------RM_PREPARE_CURSTOMER------------------------------')
        zip = self.env['res.better.zip'].search([
            ('name', 'ilike', customer['Address']['ZipCode'])], limit=1)
        # Check Sex string
        _logger.info('ZIP:')
        _logger.info(zip)
        if customer['Sex'] not in {'male', 'female'}:
            customer['Sex'] = ''
        if zip:
            state = zip.state_id
        _logger.info('ZIP_STATE:')
        _logger.info(zip.state_id.name)
        country = self.env['res.country'].search([
            ('code_alpha3', '=', customer['Address']['Country'])], limit=1)
        _logger.info('DIRECT COUNTRY:') 
        _logger.info(country)
        if not country and zip:
            country = zip.country_id
            _logger.info('ZIP COUNTRY:')
            _logger.info(country)
        # Create Street2s
        street_2 = customer['Address']['House']
        street_2 += ' ' + customer['Address']['Flat']
        street_2 += ' ' + customer['Address']['Number']
        metadata = {
            'firstname': customer['FirstName'],
            'lastname': customer['LastName1'] + ' ' + customer['LastName2'],
            'lastname2': '',
            'birthdate_date': datetime.strptime(
                customer['Birthday'], DEFAULT_ROOMMATIK_DATE_FORMAT).date(),
            'gender': customer['Sex'],
            'zip': zip.name,
            'city': customer['Address']['City'],
            'street': customer['Address']['Street'],
            'street2': street_2,
            'state_id': state.id if len(state) == 1 else False,
            'country_id': country.id if len(country) == 1 else False,
            'phone': customer['Contact']['Telephone'],
            'mobile': customer['Contact']['Mobile'],
            'email': customer['Contact']['Email'],
            'document_number': customer['IdentityDocument']['Number'],
            'document_type': customer['IdentityDocument']['Type'],
            'document_expedition_date': datetime.strptime(
                customer['IdentityDocument']['ExpeditionDate'],
                DEFAULT_ROOMMATIK_DATE_FORMAT).date(),
            }
        return {k: v for k, v in metadata.items() if v != ""}

    def rm_get_a_customer(self, customer):
        # Prepare a Customer for RoomMatik
        partner = self.search([('id', '=', customer)])
        response = {}
        response['Id'] = partner.id
        response['FirstName'] = partner.firstname
        response['LastName1'] = partner.lastname
        response['LastName2'] = ''
        response['Birthday'] = partner.birthdate_date
        response['Sex'] = partner.gender
        response['Address'] = {
            #  'Nationality': 'xxxxx'
            'Country': partner.country_id.code_alpha3,
            'ZipCode': partner.zip if partner.zip else "",
            'City': partner.city if partner.city else "",
            'Street': partner.street if partner.street else "",
            'House': partner.street2 if partner.street2 else "",
            # 'Flat': "xxxxxxx",
            # 'Number': "xxxxxxx",
            'Province': partner.state_id.name if partner.state_id.name else "",
        }
        response['IdentityDocument'] = {
            'Number': partner.document_number,
            'Type': partner.document_type,
            'ExpiryDate': "",
            'ExpeditionDate': partner.document_expedition_date,
        }
        response['Contact'] = {
            'Telephone': partner.phone if partner.phone else "",
            # 'Fax': 'xxxxxxx',
            'Mobile': partner.mobile if partner.mobile else "",
            'Email': partner.email if partner.email else "",
        }
        return response

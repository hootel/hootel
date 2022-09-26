# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
import logging


class HotelCheckinPartner(models.Model):

    _inherit = 'hotel.checkin.partner'

    @api.model
    def rm_checkin_partner(self, stay):
        _logger = logging.getLogger(__name__)
        _logger.error('ROOMMATIK PAREMETRO STAY: %s', stay)
        if not stay.get('ReservationCode'):
            reservation_obj = self.env['hotel.reservation']
            roommatik = self.env['roommatik.api']
            checkin, checkout = roommatik.normalize_checkin_date(
                stay["Arrival"],
                stay["Departure"]
            )
            vals = {
                'checkin': checkin,
                'checkout': checkout,
                'adults': stay['Adults'],
                'arrival_hour': stay['Arrival_hour'],
                'room_type_id': stay['RoomType']['Id'],
                'partner_id': stay["Customers"][0]["Id"],
                'segmentation_ids': [(6, 0, [stay['Segmentation']])],
                'channel_type': 'virtualdoor',
            }
            reservation_rm = reservation_obj.create(vals)
            stay['ReservationCode'] = reservation_rm.localizator
        else:
            reservation_rm = self.env['hotel.reservation']._get_reservations_roommatik(
                stay['ReservationCode']) # REVIEW: Puede devolver más de una reserva
        total_chekins = reservation_rm.checkin_partner_pending_count
        stay['Total'] = reservation_rm.folio_pending_amount
        stay['Paid'] = reservation_rm._computed_deposit_roommatik(stay['ReservationCode'])
        if total_chekins > 0 and len(stay["Customers"]) <= total_chekins:
            _logger.info('ROOMMATIK checkin %s customer in %s Reservation.',
                         total_chekins,
                         reservation_rm.id)
            for room_partner in stay["Customers"]:
                if room_partner['Address']['Nationality'] == 'ESP':
                    state_id = self.env['res.better.zip'].search([
                        ('name', '=', room_partner['Address']['ZipCode']),
                    ], limit=1).state_id.id
                    code_ine = self.env['code.ine'].search([
                        ('state_id', '=', state_id)
                    ], limit=1)
                else:
                    code_ine = self.env['code.ine'].search([
                        ('code', '=', room_partner['Address']['Nationality'])
                    ], limit=1)
                if not code_ine:
                    _logger.info('CODE INE not found')
                    code_ine = code_ine = self.env['code.ine'].search([
                        ('code', '=', 'ES111')
                        ], limit=1)

                nationality = self.env['res.country'].search([
                        ('code_alpha3', '=', room_partner['Address']['Nationality'])])

                checkin_partner_val = {
                    'folio_id': reservation_rm.folio_id.id,
                    'reservation_id': reservation_rm.id,
                    'partner_id': room_partner["Id"],
                    'enter_date': stay["Arrival"],
                    'exit_date': stay["Departure"],
                    'code_ine_id': code_ine.id,
                    'nationality_id': nationality.id,
                    }
                try:
                    record = self.env['hotel.checkin.partner'].create(
                        checkin_partner_val)
                    _logger.info('ROOMMATIK check-in partner: %s in \
                                                    (%s Reservation) ID:%s.',
                                 checkin_partner_val['partner_id'],
                                 checkin_partner_val['reservation_id'],
                                 record.id)
                    if not record.reservation_id.segmentation_ids:
                        record.reservation_id.update({
                            'segmentation_ids': [(6, 0, [stay['Segmentation']])]
                        })
                    record.action_on_board()
                    stay['Id'] = self.rm_obfuscate_id(record.id)
                    stay['Room'] = {}
                    stay['Room']['Id'] = reservation_rm.room_id.id
                    stay['Room']['Name'] = reservation_rm.room_id.name
                    if len(stay['Departure']) < 13:
                        stay['Departure'] = "%s %s" % (
                            stay['Departure'], reservation_rm.departure_hour)
                    _logger.info('ROOMMATIK checkin Exit Time: %s', stay['Departure'])

                    json_response = stay
                except Exception as e:
                    error_name = 'Error not create Checkin '
                    error_name += str(e)
                    json_response = {'State': error_name}
                    _logger.error('ROOMMATIK writing %s in reservation: %s).',
                                  checkin_partner_val['partner_id'],
                                  checkin_partner_val['reservation_id'])
                    return json_response

        else:
            json_response = {'State': 'Error checkin_partner_pending_count \
                                                        values do not match.'}
            _logger.error('ROOMMATIK checkin pending count do not match for \
                                        Reservation ID %s.', reservation_rm.id)
        json_response = json.dumps(json_response)
        return json_response

    @api.model
    def rm_get_stay(self, code):
        # BUSQUEDA POR LOCALIZADOR
        checkin_partner = self.search([('id', '=', self.rm_desobfuscate_id(code))])
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        if any(checkin_partner):
            arrival = checkin_partner.enter_date or default_arrival_hour
            departure = "%s %s" % (checkin_partner.exit_date,
                                   checkin_partner.reservation_id.departure_hour)
                                   # default_departure_hour)
            stay = {'Code': self.rm_obfuscate_id(checkin_partner.id)}
            stay['Id'] = self.rm_obfuscate_id(checkin_partner.id)
            stay['Room'] = {}
            stay['Room']['Id'] = checkin_partner.reservation_id.room_id.id
            stay['Room']['Name'] = checkin_partner.reservation_id.room_id.name
            stay['RoomType'] = {}
            stay['RoomType']['Id'] = checkin_partner.reservation_id.room_type_id.id
            stay['RoomType']['Name'] = checkin_partner.reservation_id.room_type_id.name
            stay['Arrival'] = arrival
            stay['Departure'] = departure
            stay['Customers'] = []
            for idx, cpi in enumerate(checkin_partner.reservation_id.checkin_partner_ids):
                stay['Customers'].append({'Customer': {}})
                stay['Customers'][idx]['Customer'] = self.env[
                    'res.partner'].rm_get_a_customer(cpi.partner_id.id)
            stay['TimeInterval'] = {}
            stay['TimeInterval']['Id'] = {}
            stay['TimeInterval']['Name'] = {}
            stay['TimeInterval']['Minutes'] = {}
            stay['Adults'] = checkin_partner.reservation_id.adults
            stay['ReservationCode'] = checkin_partner.reservation_id.localizator
            stay['Total'] = checkin_partner.reservation_id.price_total
            stay['Paid'] = checkin_partner.reservation_id.folio_id.invoices_paid
            stay['Outstanding'] = checkin_partner.reservation_id.folio_id.pending_amount
            stay['Taxable'] = checkin_partner.reservation_id.price_tax

        else:
            stay = {'Code': ""}

        json_response = json.dumps(stay)
        return json_response

    @api.model
    def rm_obfuscate_id(self, id_code):
        return int(str(id_code + 3) + '4')

    @api.model
    def rm_desobfuscate_id(self, code):
        return int(str(code)[:-1])-3

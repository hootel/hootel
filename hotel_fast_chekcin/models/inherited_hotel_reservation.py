# Copyright 2020-2021 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
import json
import logging
from datetime import datetime, timedelta, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):

    _inherit = 'hotel.reservation'

    @api.model
    def fc_get_reservation(self, code):
        # Search by localizator
        reservations = self.env['hotel.reservation'].search([(
            'localizator', '=', code)])

        if any(reservations):
            reservations = self.env['hotel.reservation'].search([(
                'folio_id.name', '=', reservations[0].folio_id.name)])
            reservations = reservations.filtered(
                lambda x: x.state in ('draft', 'confirm'))
            if any(reservations):
                reservations[0].folio_id.fc_visits += 1
                default_arrival_hour = self.env['ir.default'].sudo().get(
                    'res.config.settings', 'default_arrival_hour')
                checkin = "%s %s" % (reservations[0].checkin,
                                     default_arrival_hour)
                default_departure_hour = self.env['ir.default'].sudo().get(
                    'res.config.settings', 'default_departure_hour')
                checkout = "%s %s" % (reservations[0].checkout,
                                      default_departure_hour)
                _logger.info('FastCheckin serving Folio: %s', reservations.ids)
                json_response = {
                    'Reservation': {
                        'Localizator': reservations[0].localizator,
                        'FolioId': reservations[0].folio_id.id,
                        'FolioName': reservations[0].folio_id.name,
                        'Arrival': checkin,
                        'Departure': checkout,
                        'partner_id': reservations[0].partner_id.id,
                        'PartnerFirstName': reservations[
                            0].partner_id.firstname,
                        'PartnerLastName': reservations[0].partner_id.lastname,
                        'AmountTotal': reservations[0].folio_id.amount_total,
                        'DepositAmount': reservations[
                            0].folio_id.amount_total - reservations[
                                0].folio_pending_amount,
                        'PendingAmount': reservations[0].folio_pending_amount,
                        'HidePrices': reservations[0].folio_id.hide_pay,
                    }
                }
                for i, line in enumerate(reservations):
                    total_chekins = line.checkin_partner_pending_count
                    json_response['Reservation'].setdefault(
                        'Rooms', []).append({
                            'Id': line.id,
                            'ReservationId': reservations[0].folio_id.id,
                            'Arrival': line.checkin,
                            'Departure': line.checkout,
                            'Nights': line.nights,
                            'Adults': line.adults,
                            'Children': line.children,
                            'IsAvailable': total_chekins > 0,
                            'Price': line.price_total,
                            'RoomTypeId': line.room_type_id.id,
                            'RoomTypeName': line.room_type_id.name,
                            'RoomName': line.room_id.name,
                            'checkin_partner_count': line.checkin_partner_count,
                            'checkin_partner_pending_count':
                                line.checkin_partner_pending_count,
                            'Checkins': [],
                            # 'RoomCheckins': line.checkin_partner_ids
                        })
                    if line.checkin_partner_count > 0:
                        for checkin in line.checkin_partner_ids:
                            json_response['Reservation'][
                                'Rooms'][i]['Checkins'].append({
                                    'mobile': checkin.mobile,
                                    'birthdate_date': checkin.birthdate_date,
                                    'code_ine_id2': checkin.code_ine_id.name,
                                    'code_ine_id': checkin.code_ine_id.code,
                                    'name': checkin.name,
                                    'lastname': checkin.lastname,
                                    'partner_id': checkin.partner_id.id,
                                    'reservation_id': checkin.id,
                                    })
            else:
                _logger.warning('FastCheckin Search cancedel reservation %s',
                                code)
                json_response = {'Error': 'Canceled reservation ' + str(code)}
        else:
            _logger.warning('FastCheckin Not Found reservation %s', code)
            json_response = {'Error': 'Not Found ' + str(code)}
        return json.dumps(json_response)

    @api.multi
    def urlcodefc(self, fecha, localizator):
        # Calculate a Secure Code to create url.
        dcontrol = 0
        for i, char in enumerate(localizator):
            dcontrol += int(char)

        compan = self.env.user.company_id
        d = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        delay = compan.fc_seeed_code * 100
        dtxt = float(d.strftime('%s.%%06d') % d.microsecond) + delay
        dtxt = repr(dtxt)[4:8]
        patron = 'ahkosuwxyz'
        for i, char in enumerate(dtxt):
            dtxt = dtxt.replace(dtxt[i], patron[int(char)])
            dcontrol += int(char)
        dcontrol = patron[dcontrol % 9]
        return dtxt+dcontrol

    @api.multi
    def fc_url_text(self, localizator, checkout):
        compan = self.env.user.company_id
        url = compan.fc_server + '/'
        url += str(compan.fc_server_id) + '/'
        url += localizator + '/'
        url += self.urlcodefc(checkout, localizator)
        return url

    @api.multi
    def _compute_fc_url(self):
        for res in self:
            res.fc_url = self.fc_url_text(res.localizator, res.checkout)

    fc_url = fields.Char('Fast Checkin URL',
                         compute='_compute_fc_url')

    @api.multi
    def fc_next_localizator(self, dias):
        # Search nexts localizators
        s_date = date.today()+timedelta(days=-1)
        s_date2 = date.today()+timedelta(days=dias)
        _logger.info('FASTCHECKIN search Localizators FROM %s To %s Dates.',
                     s_date, s_date2)
        localizators = self.env['hotel.reservation'].search([
            ('checkin', '>=', s_date),
            ('checkin', '<', s_date2)])
        json_response = []
        for localizator in localizators:
            json_response.append([{
                'Id': localizator.id,
                'Localizator': localizator.localizator,
                'Checkin': localizator.checkin,
                'Estate': localizator.state,
                }])
        return json.dumps(json_response)

    @api.multi
    def fast_checkin_view_mail(self):
        return self.folio_id.fast_checkin_view_mail()

    @api.multi
    def send_fast_checkin_mail(self):
        return self.folio_id.send_fast_checkin_mail()

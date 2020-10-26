# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
import json
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):

    _inherit = 'hotel.reservation'

    @api.model
    def _computed_deposit_roommatik(self, rm_localizator):
        reservations = self.env['hotel.reservation'].search([
            ('localizator', '=', rm_localizator)])
        folio = reservations[0].folio_id
        # We dont have the payments by room, that's why we have to computed
        # the proportional deposit part if the folio has more rooms that the
        # reservations code (this happens when in the same folio are
        # reservations with different checkins/outs convinations)
        if not folio.hide_pay:
            return 0
        else:
            return folio.invoices_paid

    @api.multi
    def _compute_to_pay(self):
        folio = self.folio_id
        onboard_reservations = folio.room_lines.filtered(
            lambda r: r.state in ['done', 'booking']
        )
        consumed = sum(onboard_reservations.mapped('price_total'))
        paid_in_folio = folio.invoices_paid
        total_in_folio = folio.amount_total
        to_pay_folio = total_in_folio - (paid_in_folio - consumed)
        to_pay_reservation = self.price_total - to_pay_folio
        if not folio.hide_pay:
            return 0
        else:
            if to_pay_reservation > to_pay_folio:
                return to_pay_folio
            else:
                return self.price_total

    @api.model
    def rm_get_reservation(self, code):
        # Search by localizator or Folio
        reservations = self._get_reservations_roommatik(code)
        _logger.warning('ROOMMATIK rm_get_reservation Encontradas: %s',
                        len(reservations))

        reservations = reservations.filtered(
            lambda x: x.state in ('draft', 'confirm', 'booking'))

        _logger.warning('ROOMMATIK rm_get_reservation Filtradas: %s',
                        len(reservations))

        if any(reservations):
            default_arrival_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_arrival_hour')
            checkin = "%s %s" % (reservations[0].checkin,
                                 default_arrival_hour)
            default_departure_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour')
            checkout = "%s %s" % (reservations[0].checkout,
                                  default_departure_hour)
            _logger.info('ROOMMATIK serving  Folio: %s', reservations.ids)
            json_response = {
                'Reservation': {
                    'Id': reservations[0].localizator,
                    'Arrival': checkin,
                    'Departure': checkout,
                    'Deposit': self._computed_deposit_roommatik(code)
                }
            }
            for i, line in enumerate(reservations):
                total_chekins = line.checkin_partner_pending_count
                json_response['Reservation'].setdefault('Rooms', []).append({
                    'Id': line.id,
                    'Adults': line.adults,
                    'IsAvailable': total_chekins > 0,
                    # IsAvailable “false” Rooms not need check-in
                    'Price': line._compute_to_pay(),
                    'RoomTypeId': line.room_type_id.id,
                    'RoomTypeName': line.room_type_id.name,
                    'RoomName': line.room_id.name,
                })
        else:
            _logger.warning('ROOMMATIK Not Found reservation search  %s', code)
            json_response = {'Error': 'Not Found ' + str(code)}
        return json.dumps(json_response)

    @api.model
    def _get_reservations_roommatik(self, code):
        return self.env['hotel.reservation'].search([
            '|', ('localizator', '=', code),
            ('folio_id.name', '=', code)])

    @api.model
    def rm_get_departures(self):
        reservations = self.env['hotel.reservation'].search([
            ('checkout', '=', fields.Date.today())])
        return json.dumps(reservations.mapped('localizator'))

    @api.model
    def rm_get_arrivals(self):
        reservations = self.env['hotel.reservation'].search([
            ('checkin', '=', fields.Date.today())])
        return json.dumps(reservations.mapped('localizator'))

    @api.multi
    def _compute_duplicate_keys(self):
        if self.checkin_partner_count < 1:
            self.duplicate_keys = _('No code yet')
        else:
            for res in self:
                ch_partner = self.checkin_partner_ids[0]
                res.duplicate_keys = ch_partner.rm_obfuscate_id(ch_partner.id)

    duplicate_keys = fields.Char('Code to duplicate key',
                                 compute='_compute_duplicate_keys')

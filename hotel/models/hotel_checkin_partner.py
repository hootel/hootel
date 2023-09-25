# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)


class HotelCheckinPartner(models.Model):
    _name = 'hotel.checkin.partner'

    def _default_reservation_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation
        return False

    def _default_partner_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            partner_ids = []
            if reservation.folio_id:
                for room in reservation.folio_id.room_lines:
                    partner_ids.append(room.mapped(
                            'checkin_partner_ids.partner_id.id'))
            if 'checkin_partner_ids' in self.env.context:
                for checkin in self.env.context['checkin_partner_ids']:
                    if checkin[0] == 0:
                        partner_ids.append(checkin[2].get('partner_id'))
            if self._context.get('include_customer') and reservation.partner_id.id \
                    not in partner_ids and not reservation.partner_id.is_company:
                return reservation.partner_id
        return False

    def _default_folio_id(self):
        if 'folio_id' in self.env.context:
            folio = self.env['hotel.folio'].browse([
                self.env.context['folio_id']
            ])
            return folio
        if 'reservation_id' in self.env.context:
            folio = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ]).folio_id
            return folio
        return False

    def _default_enter_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation.checkin
        return False

    def _default_exit_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].browse([
                self.env.context['reservation_id']
            ])
            return reservation.checkout
        return False

    partner_id = fields.Many2one('res.partner', default=_default_partner_id,
                                 required=True)
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    reservation_id = fields.Many2one(
        'hotel.reservation', default=_default_reservation_id)
    folio_id = fields.Many2one('hotel.folio',
                               default=_default_folio_id,
                               readonly=True, required=True)
    enter_date = fields.Date(default=_default_enter_date, required=True)
    exit_date = fields.Date(default=_default_exit_date, required=True)
    arrival_hour = fields.Char('Arrival Hour',
                               help="Default Arrival Hour (HH:MM)")
    departure_hour = fields.Char('Departure Hour',
                                 help="Default Departure Hour (HH:MM)")
    auto_booking = fields.Boolean('Get in Now', default=False)
    state = fields.Selection([('draft', 'Pending Entry'),
                              ('booking', 'On Board'),
                              ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='onchange')

    @api.model
    def create(self, vals):
        record = super(HotelCheckinPartner, self).create(vals)
        if vals.get('auto_booking', False):
            record.action_on_board()
        return record

    # Validation for Departure date is after arrival date.
    @api.multi
    @api.constrains('exit_date', 'enter_date')
    def _check_exit_date(self):
        for record in self:
            date_in = fields.Date.from_string(record.enter_date)
            date_out = fields.Date.from_string(record.exit_date)
            if date_out < date_in:
                raise models.ValidationError(
                    _('Departure date (%s) is prior to arrival on %s') %
                    (date_out, date_in))

    @api.onchange('enter_date', 'exit_date')
    def _onchange_enter_date(self):
        date_in = fields.Date.from_string(self.enter_date)
        date_out = fields.Date.from_string(self.exit_date)
        if date_out <= date_in:
            date_out = date_in + datetime.timedelta(days=1)
            self.update({'exit_date': date_out})
            raise ValidationError(
                _('Departure date, is prior to arrival. Check it now. %s') %
                date_out)

    @api.multi
    @api.onchange('partner_id')
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                if record.partner_id.is_company:
                    raise models.ValidationError(
                        _('A Checkin Guest is configured like a company, \
                          modify it in contact form if its a mistake'))
                indoor_partner_ids = record.reservation_id.checkin_partner_ids.\
                    filtered(lambda r: r.id != record.id).mapped('partner_id.id')
                if indoor_partner_ids.count(record.partner_id.id) > 1:
                    record.partner_id = None
                    raise models.ValidationError(
                        _('This guest is already registered in the room'))

    @api.multi
    def action_on_board(self):
        for record in self:
            if record.reservation_id.checkin > fields.Date.today():
                raise models.ValidationError(
                    _('It is not yet checkin day!'))
            hour = record._get_arrival_hour()
            vals = {
                'state': 'booking',
                'arrival_hour': hour,
            }
            record.update(vals)
            if record.reservation_id.state == 'confirm':
                record.reservation_id.state = 'booking'
                if record.reservation_id.splitted:
                    master_reservation = record.reservation_id.parent_reservation or record.reservation_id
                    splitted_reservs = self.env['hotel.reservation'].search([
                        ('splitted', '=', True),
                        '|',
                        ('parent_reservation', '=', master_reservation.id),
                        ('id', '=', master_reservation.id),
                        ('folio_id', '=', record.folio_id.id),
                        ('id', '!=', record.id),
                        ('state', '=', 'confirm')
                    ])
                    if splitted_reservs:
                        splitted_reservs.update({'state': 'booking'})
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.multi
    def action_done(self):
        for record in self:
            if record.state == 'booking':
                hour = record._get_departure_hour()
                vals = {
                    'state': 'done',
                    'departure_hour': hour,
                }
                record.update(vals)
        return True

    def _get_arrival_hour(self):
        self.ensure_one()
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Datetime.context_timestamp(
            self.with_context(tz=tz_hotel),
            datetime.datetime.strptime(fields.Date.today(),
                                       DEFAULT_SERVER_DATE_FORMAT))
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        if self.reservation_id.checkin < today.strftime(DEFAULT_SERVER_DATE_FORMAT):
            return default_arrival_hour
        now = fields.Datetime.context_timestamp(
            self.with_context(tz=tz_hotel),
            datetime.datetime.strptime(fields.Datetime.now(),
                                       DEFAULT_SERVER_DATETIME_FORMAT))
        arrival_hour = now.strftime("%H:%M")
        return arrival_hour

    def _get_departure_hour(self):
        self.ensure_one()
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Datetime.context_timestamp(
            self.with_context(tz=tz_hotel),
            datetime.datetime.strptime(fields.Date.today(),
                                       DEFAULT_SERVER_DATE_FORMAT))
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        if self.reservation_id.checkout < today.strftime(DEFAULT_SERVER_DATE_FORMAT):
            return default_departure_hour
        now = fields.Datetime.context_timestamp(
            self.with_context(tz=tz_hotel),
            datetime.datetime.strptime(fields.Datetime.now(),
                                       DEFAULT_SERVER_DATETIME_FORMAT))
        departure_hour = now.strftime("%H:%M")
        return departure_hour

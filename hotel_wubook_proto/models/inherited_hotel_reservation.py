# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from datetime import datetime, timedelta
from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from ..wubook import (
    DEFAULT_WUBOOK_DATE_FORMAT,
    WUBOOK_STATUS_CONFIRMED,
    WUBOOK_STATUS_WAITING,
    WUBOOK_STATUS_REFUSED,
    WUBOOK_STATUS_ACCEPTED,
    WUBOOK_STATUS_CANCELLED,
    WUBOOK_STATUS_CANCELLED_PENALTY)
from odoo.addons.hotel import date_utils
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.depends('wrid', 'wchannel_id')
    def _is_from_channel(self):
        for record in self:
            record.wis_from_channel = (record.wrid and record.wrid != ''
                                       and record.wchannel_id)

    wrid = fields.Char("WuBook Reservation ID", readonly=True)
    wchannel_id = fields.Many2one('wubook.channel.info',
                                  string='WuBook Channel ID',
                                  readonly=True)
    wchannel_reservation_code = fields.Char("WuBook Channel Reservation Code",
                                            readonly=True)
    wis_from_channel = fields.Boolean('WuBooK Is From Channel',
                                      compute=_is_from_channel, store=False,
                                      readonly=True)
    to_read = fields.Boolean('To Read', default=False)

    wstatus = fields.Selection([
        ('0', 'No WuBook'),
        (str(WUBOOK_STATUS_CONFIRMED), 'Confirmed'),
        (str(WUBOOK_STATUS_WAITING), 'Waiting'),
        (str(WUBOOK_STATUS_REFUSED), 'Refused'),
        (str(WUBOOK_STATUS_ACCEPTED), 'Accepted'),
        (str(WUBOOK_STATUS_CANCELLED), 'Cancelled'),
        (str(WUBOOK_STATUS_CANCELLED_PENALTY), 'Cancelled with penalty')],
                               string='WuBook Status', default='0',
                               readonly=True)
    wstatus_reason = fields.Char("WuBook Status Reason", readonly=True)
    wcustomer_notes = fields.Text(related='folio_id.wcustomer_notes')

    @api.multi
    def save_wubook_availability(self, wavails):
        avail_obj = self.env['hotel.virtual.room.availability']
        vroom_obj = self.env['hotel.virtual.room']
        for wavail in wavails:
            for wrid, days in wavails.iteritems():
                vroom = vroom_obj.search([('wrid', '=', wrid)], limit=1)
                if vroom:
                    for date, avail in days.iteritems():
                        cavail = avail_obj.search([
                            ('virtual_room_id', '=', vroom.id),
                            ('date', '=', date)
                        ])
                        if cavail:
                            cavail.with_context({
                                'wubook_action': False,
                            }).write({
                                'avail': avail,
                                'wpushed': True,
                            })
                        else:
                            navail = avail_obj.create({
                                'virtual_room_id': vroom.id,
                                'date': date,
                                'avail': avail,
                                'wpushed': True,
                            })
                            if not navail:
                                raise ValidationError(
                                        "Can't update availability in Odoo!")

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            reserv_obj = self.env['hotel.reservation']
            rooms_avail = reserv_obj.get_wubook_availability(
                vals['checkin'],
                vals['checkout'],
                vals['product_id'],
                dbchanged=False)
            _logger.info("DISPONIBILIDAD CREATE")
            _logger.info(rooms_avail)
            if any(rooms_avail):
                wres = self.env['wubook'].update_availability(rooms_avail)
                if not wres:
                    raise ValidationError("Can't update availability \
                                                            on WuBook")
                self.save_wubook_availability(rooms_avail)

        res = super(HotelReservation, self).create(vals)
        return res

#     @api.multi
#     def read(self, fields=None, load='_classic_read'):
#         self.to_read = False
#         return super(HotelReservation, self).read(fields=fields, load=load)

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account() and \
                (vals.get('checkin') or vals.get('checkout') or
                 vals.get('product_id') or vals.get('state')):
            older_vals = []
            new_vals = []
            for record in self:
                prod_id = False
                if record.product_id:
                    prod_id = record.product_id.id
                older_vals.append({
                    'checkin': record.checkin,
                    'checkout': record.checkout,
                    'product_id': prod_id,
                })
                new_vals.append({
                    'checkin': vals.get('checkin', record.checkin),
                    'checkout': vals.get('checkout', record.checkout),
                    'product_id': vals.get('product_id', prod_id),
                })

            res = super(HotelReservation, self).write(vals)

            for i in range(0, len(older_vals)):
                navails = self._generate_wubook_diff_avail(older_vals[i],
                                                           new_vals[i])
                _logger.info("DISPONIBILIDAD WRITE")
                _logger.info(navails)
                if any(navails):
                    # Push avail to Wubook
                    wres = self.env['wubook'].update_availability(navails)
                    if not wres:
                        raise ValidationError("Can't update availability \
                                                                on WuBook")
                    # Update Availability in Odoo
                    self.save_wubook_availability(navails)
        else:
            res = super(HotelReservation, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        vals = {}
        for record in self:
            vals.update({
                'checkin': record.checkin,
                'checkout': record.checkout,
                'product_id': record.product_id.id,
            })
        res = super(HotelReservation, self).unlink()
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vals = {}
            for record in vals:
                rooms_avail = self.get_wubook_availability(
                    record['checkin'],
                    record['checkout'],
                    record['product_id'])
                _logger.info("DISPONIBILIDAD UNLINK")
                _logger.info(rooms_avail)
                if any(rooms_avail):
                    wres = wubook_obj.update_availability(rooms_avail)
                    if not wres:
                        raise ValidationError("Can't update availability \
                                                                on WuBook")
                    self.save_wubook_availability(rooms_avail)
        return res

    @api.model
    def _generate_wubook_diff_avail(self, older_vals, new_vals):
        old_rooms_avail = []
        new_rooms_avail = []
        if older_vals['checkin'] and older_vals['checkout'] and \
                older_vals['product_id']:
            old_rooms_avail = self.get_wubook_availability(
                older_vals['checkin'],
                older_vals['checkout'],
                older_vals['product_id'])
        if new_vals['checkin'] and new_vals['checkout'] and \
                new_vals['product_id']:
            new_rooms_avail = self.get_wubook_availability(
                new_vals['checkin'],
                new_vals['checkout'],
                new_vals['product_id'])
        # Merge Old & New Dicts (Updating Old Dict)
        for newitem in new_rooms_avail:
            found = False
            for olditem in old_rooms_avail:
                if olditem['id'] == newitem['id']:
                    for newdays in newitem['days']:
                        foundday = False
                        for olddays in olditem['days']:
                            if olddays['date'] == newdays['date']:
                                olddays.update(newdays)
                                foundday = True
                        if not foundday:
                            olditem['days'].append(newdays)
                    found = True
            if not found:
                old_rooms_avail.append(newitem)
        return old_rooms_avail

    @api.multi
    def action_cancel(self):
        res = super(HotelReservation, self).action_cancel()
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            partner_id = self.env['res.users'].browse(self.env.uid).partner_id
            wubook_obj = self.env['wubook']
            for record in self:
                    # Only can cancel reservations created directly in wubook
                    if record.wrid and record.wrid != '' and \
                            not record.wchannel_id and \
                            record.wstatus in ['1', '2', '4']:
                        wres = wubook_obj.cancel_reservation(
                            record.wrid,
                            'Cancelled by %s' % partner_id.name)
                        if not wres:
                            raise ValidationError("Can't cancel reservation \
                                                                    on WuBook")
        return res

    @api.multi
    def confirm(self):
        self.mark_as_readed()
        return super(HotelReservation, self).confirm()

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        res = super(HotelReservation, self).generate_copy_values(
                                            checkin=checkin, checkout=checkout)
        res.update({
            'wrid': self.wrid,
            'wchannel_id': self.wchannel_id,
            'wchannel_reservation_code': self.wchannel_reservation_code,
            'wis_from_channel': self.wis_from_channel,
            'to_read': self.to_read,
            'wstatus': self.wstatus,
            'wstatus_reason': self.wstatus_reason,
            'wcustomer_notes': self.wcustomer_notes,
        })
        return res

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            record.mark_as_readed()
            if record.state == 'cancelled':
                return
            else:
                return super(HotelReservation, record).\
                                                action_reservation_checkout()

    @api.multi
    def mark_as_readed(self):
        for record in self:
            record.write({'to_read': False})

    @api.model
    def get_wubook_availability(self, checkin, checkout, product_id,
                                dbchanged=True):
        date_start = date_utils.get_datetime(checkin)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(checkin, checkout, hours=False)

        vroom_obj = self.env['hotel.virtual.room']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']

        rooms_avail = []
        vrooms = vroom_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for vroom in vrooms:
            if vroom.wrid and vroom.wrid != '':
                rdays = []
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(
                                                DEFAULT_SERVER_DATETIME_FORMAT)
                    avail = len(vroom_obj.check_availability_virtual_room(
                        ndate_str,
                        ndate_str,
                        virtual_room_id=vroom.id))
                    if not dbchanged:
                        avail = avail - 1
                    max_avail = vroom.total_rooms_count
                    vroom_avail_id = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', ndate_str)], limit=1)
                    if vroom_avail_id and vroom_avail_id.wmax_avail >= 0:
                        max_avail = vroom_avail_id.wmax_avail
                    avail = max(
                            min(avail, vroom.total_rooms_count, max_avail), 0)
                    rdays.append({
                        'date': ndate_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': avail,
                    })
                ravail = {'id': vroom.wrid, 'days': rdays}
                rooms_avail.append(ravail)

        return rooms_avail

    @api.onchange('checkin', 'checkout', 'product_id')
    def on_change_checkin_checkout_product_id(self):
        if not self.wis_from_channel:
            return super(HotelReservation, self).\
                                        on_change_checkin_checkout_product_id()

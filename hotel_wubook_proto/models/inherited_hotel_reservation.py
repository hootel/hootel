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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from ..wubook import DEFAULT_WUBOOK_DATE_FORMAT, WUBOOK_STATUS_CONFIRMED, \
    WUBOOK_STATUS_WAITING, WUBOOK_STATUS_REFUSED, WUBOOK_STATUS_ACCEPTED, \
    WUBOOK_STATUS_CANCELLED, WUBOOK_STATUS_CANCELLED_PENALTY
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.depends('wrid', 'wchannel_id')
    def _is_from_channel(self):
        for record in self:
            record.wis_from_channel = (record.wrid and record.wrid != '' and record.wchannel_id)

    wrid = fields.Char("WuBook Reservation ID", readonly=True)
    wchannel_id = fields.Many2one('wubook.channel.info',
                                  string='WuBook Channel ID',
                                  readonly=True)
    wchannel_reservation_code = fields.Char("WuBook Channel Reservation Code", readonly=True)
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

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True) and self.env['wubook'].is_valid_account():
            rooms_avail = self.env['hotel.reservation'].get_wubook_availability(vals['checkin'],
                                                                                vals['checkout'],
                                                                                vals['product_id'],
                                                                                dbchanged=False)
            _logger.info("DISPONIBILIDAD CREATE")
            _logger.info(rooms_avail)
            if any(rooms_avail):
                wres = self.env['wubook'].update_availability(rooms_avail)
                if not wres:
                    raise ValidationError("Can't update availability on WuBook")
        res = super(HotelReservation, self).create(vals)
        return res

#     @api.multi
#     def read(self, fields=None, load='_classic_read'):
#         self.to_read = False
#         return super(HotelReservation, self).read(fields=fields, load=load)

    @api.multi
    def write(self, vals):
        res = super(HotelReservation, self).write(vals)
        if self._context.get('wubook_action', True) and self.env['wubook'].is_valid_account():
            for record in self:
                older_vals = {
                    'checkin': record.checkin,
                    'checkout': record.checkout,
                    'product_id': record.product_id.id,
                }
                new_vals = {
                    'checkin': vals.get('checkin'),
                    'checkout': vals.get('checkout'),
                    'product_id': vals.get('product_id'),
                }
                if new_vals['checkin'] or new_vals['checkout'] or new_vals['product_id']:
                    old_rooms_avail = []
                    new_rooms_avail = []
                    if older_vals['checkin'] and older_vals['checkout'] and older_vals['product_id']:
                        old_rooms_avail = self.get_wubook_availability(
                            older_vals['checkin'],
                            older_vals['checkout'],
                            older_vals['product_id'])
                    if new_vals['checkin'] and new_vals['checkout'] and new_vals['product_id']:
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
                    # Push avail
                    if any(old_rooms_avail):
                        _logger.info("DISPONIBILIDAD WRITE")
                        _logger.info(old_rooms_avail)
                        wres = self.env['wubook'].update_availability(old_rooms_avail)
                        if not wres:
                            raise ValidationError("Can't update availability on WuBook")
        return res

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True) and self.env['wubook'].is_valid_account():
            checkin = self.checkin
            checkout = self.checkout
            product_id = self.product_id.id
            res = super(HotelReservation, self).unlink()
            rooms_avail = self.get_wubook_availability(checkin,
                                                       checkout,
                                                       product_id)
            _logger.info("DISPONIBILIDAD UNLINK")
            _logger.info(rooms_avail)
            if any(rooms_avail):
                wres = self.env['wubook'].update_availability(rooms_avail)
                if not wres:
                    raise ValidationError("Can't update availability on WuBook")
        return res

    @api.multi
    def action_cancel(self):
        res = super(HotelReservation, self).action_cancel()
        if self._context.get('wubook_action', True) and self.env['wubook'].is_valid_account():
            partner_id = self.env['res.users'].browse(self.env.uid).partner_id
            for record in self:
                    if self.wrid and self.wrid != '' and not self.wchannel_id and \
                            self.wstatus in ['1', '2', '4']:     # Only can cancel reservations created directly in wubook
                        wres = self.env['wubook'].cancel_reservation(record.wrid,
                                                                     'Cancelled by %s' % partner_id.name)
                        if not wres:
                            raise ValidationError("Can't cancel reservation on WuBook")
                    rooms_avail = self.get_wubook_availability(record.checkin,
                                                               record.checkout,
                                                               record.product_id.id)
                    _logger.info("DISPONIBILIDAD CANCEL")
                    _logger.info(rooms_avail)
                    if any(rooms_avail):
                        wres = self.env['wubook'].update_availability(rooms_avail)
                        if not wres:
                            raise ValidationError("Can't update availability on WuBook")
        return res

    @api.multi
    def confirm(self):
        self.mark_as_readed()
        return super(HotelReservation, self).confirm()

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        res = super(HotelReservation, self).generate_copy_values(checkin=checkin, checkout=checkout)
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
                return super(HotelReservation, record).action_reservation_checkout()

    @api.multi
    def mark_as_readed(self):
        for record in self:
            record.write({'to_read': False})

    @api.model
    def get_wubook_availability(self, checkin, checkout, product_id, dbchanged=True):
        date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT)
        date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT)
        date_diff = abs((date_start - date_end).days)

        hotel_vroom_obj = self.env['hotel.virtual.room']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availabity']

        rooms_avail = []
        vrooms = hotel_vroom_obj.search([('room_ids.product_id', '=', product_id)])
        for vroom in vrooms:
            if vroom.wrid and vroom.wrid != '':
                rdays = []
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    avail = len(hotel_vroom_obj.check_availability_virtual_room(ndate_str,
                                                                                ndate_str,
                                                                                virtual_room_id=vroom.id))
                    if not dbchanged:
                        avail = avail - 1
                    vroom_avail_id = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', ndate_str)], limit=1)
                    max_avail = vroom.total_rooms_count
                    if vroom_avail_id:
                        max_avail = vroom_avail_id.avail
                    avail = min(avail, max_avail)
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
            return super(HotelReservation, self).on_change_checkin_checkout_product_id()

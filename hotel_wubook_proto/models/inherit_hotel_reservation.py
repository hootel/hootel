# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
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
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from ..wubook import DEFAULT_WUBOOK_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.depends('wrid', 'wchannel_id')
    def _is_from_channel(self):
        for record in self:
            record.wis_from_channel = (record.wrid != 'none' and record.wchannel_id)

    wrid = fields.Char("WuBook Reservation ID", default="none", readonly=True)
    wchannel_id = fields.Many2one('wubook.channel.info', string='WuBook Channel ID',
                                  readonly=True)
    wchannel_reservation_code = fields.Char("WuBook Channel Reservation Code",
                                            default='none', readonly=True)
    wis_from_channel = fields.Boolean('WuBooK Is From Channel',
                                      compute=_is_from_channel, store=False,
                                      readonly=True)
    to_read = fields.Boolean('To Read', default=False)

    wstatus = fields.Selection([
        ('0', 'No WuBook'),
        ('1', 'Confirmed'),
        ('2', 'Waiting'),
        ('3', 'Refused'),
        ('4', 'Accepted'),
        ('5', 'Cancelled'),
        ('6', 'Cancelled with penalty')], string='WuBook Status', default='0', readonly=True)
    wstatus_reason = fields.Char("WuBook Status Reason", readonly=True)

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True):
            rooms_avail = self.get_availability(vals['checkin'],
                                                vals['checkout'],
                                                vals['product_id'])
            self.env['wubook'].update_availability(rooms_avail)
        res = super(HotelReservation, self).create(vals)
        return res

#     @api.multi
#     def read(self, fields=None, load='_classic_read'):
#         self.to_read = False
#         return super(HotelReservation, self).read(fields=fields, load=load)

    @api.multi
    def write(self, vals):
        older_vals = {
            'checkin': self.checkin,
            'checkout': self.checkout,
            'product_id': self.product_id.id,
        }
        new_vals = {
            'checkin': vals.get('checkin'),
            'checkout': vals.get('checkout'),
            'product_id': vals.get('product_id'),
        }
        if self._context.get('wubook_action', True):
            old_rooms_avail = []
            new_rooms_avail = []
            if older_vals['checkin'] and older_vals['checkout'] and older_vals['product_id']:
                old_rooms_avail = self.get_availability(older_vals['checkin'],
                                                        older_vals['checkout'],
                                                        older_vals['product_id'])
            if new_vals['checkin'] and new_vals['checkout'] and new_vals['product_id']:
                new_rooms_avail = self.get_availability(new_vals['checkin'],
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
                self.env['wubook'].update_availability(old_rooms_avail)
        return super(HotelReservation, self).write(vals)

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True):
            partner_id = self.env['res.users'].browse(self.env.uid).partner_id
            for record in self:
                if self.wrid != 'none' and not self.wchannel_id:
                    self.env['wubook'].cancel_reservation(record.wrid,
                                                          'Cancelled by %s' % partner_id.name)
            rooms_avail = self.get_availability(self.checkin,
                                                self.checkout,
                                                self.product_id.id)
            self.env['wubook'].update_availability(rooms_avail)
        return super(HotelReservation, self).unlink()

    @api.multi
    def action_cancel(self):
        res = super(HotelReservation, self).action_cancel()
#         partner_id = self.env['res.users'].browse(self.env.uid).partner_id
#         for record in self:
#                 if self.wrid != 'none' and not self.wchannel_id and \
#                         self.wstatus in ['1', '2', '4']:     # Only can cancel reservations created directly in wubook
#                     self.env['wubook'].cancel_reservation(record.wrid,
#                                                           'Cancelled by %s' % partner_id.name)
        return res

    @api.multi
    def mark_as_read(self):
        for record in self:
            record.to_read = False

    @api.model
    def get_availability(self, checkin, checkout, product_id):
        date_start = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT)
        date_end = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT)
        date_diff = abs((date_start - date_end).days)

        hotel_vroom_obj = self.env['hotel.virtual.room']
        rooms_avail = []
        vrooms = self.env['hotel.virtual.room'].search([('room_ids.product_id', '=', product_id)])
        for vroom in vrooms:
            rdays = []
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                avail = len(hotel_vroom_obj.check_availability_virtual_room(ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                                                            ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                                                            vroom.id))
                avail = min(avail, vroom.max_real_rooms)
                rdays.append({
                    'date': ndate.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': avail,
                })
            ravail = {'id': vroom.wrid, 'days': rdays}
            rooms_avail.append(ravail)

        return rooms_avail

    @api.onchange('checkin', 'checkout', 'product_id')
    def on_change_checkin_checkout_product_id(self):
        if not self.wis_from_channel:
            return super(HotelReservation, self).on_change_checkin_checkout_product_id()

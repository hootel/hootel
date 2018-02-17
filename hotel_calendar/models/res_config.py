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
from openerp import models, fields, api
from odoo.addons.hotel import date_utils


class HotelConfiguration(models.TransientModel):
    _inherit = 'hotel.config.settings'

    color_pre_reservation = fields.Char('Pre-reservation', default='#A4A4A4')
    color_reservation = fields.Char('Confirmed Reservation ',
                                    default='#4E9DC4')
    color_reservation_pay = fields.Char('Paid Reservation', default='#66CCFF')
    color_stay = fields.Char('Checkin', default='#b40606')
    color_stay_pay = fields.Char('Paid Checkin', default='#54d12b')
    color_checkout = fields.Char('Checkout', default='#FF0000')
    color_dontsell = fields.Char('Dont Sell', default='#000000')
    color_staff = fields.Char('Staff', default='#FF9933')
    color_to_assign = fields.Char('Ota Reservation to Assign',
                                  default='#DFFF00')
    color_payment_pending = fields.Char('Letter Payment Pending', default='#f70f0f')
    color_letter_pre_reservation = fields.Char('Letter  Pre-reservation', default='#000000')
    color_letter_reservation = fields.Char('Letter  Confirmed Reservation ',
                                    default='#000000')
    color_letter_reservation_pay = fields.Char('Letter Paid Reservation', default='#000000')
    color_letter_stay = fields.Char('Letter Checkin', default='#FFF')
    color_letter_stay_pay = fields.Char('Letter Stay Pay', default='#000000')
    color_letter_checkout = fields.Char('Letter Checkout', default='#FFF')
    color_letter_dontsell = fields.Char('Letter Dont Sell', default='#FFF')
    color_letter_staff = fields.Char('Letter Staff', default='#000000')
    color_letter_to_assign = fields.Char('Letter Ota to Assign',
                                  default='#000000')
    color_letter_payment_pending = fields.Char('Letter Payment Pending', default='#000000')

    @api.multi
    def set_parity_pricelist_id(self):
        pricelist_id = super(
                            HotelConfiguration, self).set_parity_pricelist_id()
        self.env['virtual.room.pricelist.cached'].search([]).unlink()

        pricelist_items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id)
        ])
        vroom_obj = self.env['hotel.virtual.room']
        for pitem in pricelist_items:
            date_start = pitem.date_start
            product_tmpl_id = pitem.product_tmpl_id.id
            fixed_price = pitem.fixed_price
            vroom = vroom_obj.search([
                ('product_id.product_tmpl_id', '=', product_tmpl_id),
                ('date_start', '>=', date_utils.now().strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT))
            ], limit=1)
            vroom_pr_cached_obj.create({
                'virtual_room_id': vroom.id,
                'date': date_start,
                'price': prod_price,
            })

        return pricelist_id

    @api.multi
    def set_color_pre_reservation(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_pre_reservation', self.color_pre_reservation)

    @api.multi
    def set_color_reservation(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_reservation', self.color_reservation)

    @api.multi
    def set_color_reservation_pay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_reservation_pay', self.color_reservation_pay)

    @api.multi
    def set_color_stay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_stay', self.color_stay)

    @api.multi
    def set_color_stay_pay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_stay_pay', self.color_stay_pay)

    @api.multi
    def set_color_checkout(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_checkout', self.color_checkout)

    @api.multi
    def set_color_dontsell(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_dontsell', self.color_dontsell)

    @api.multi
    def set_color_staff(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_staff', self.color_staff)

    @api.multi
    def set_color_to_assign(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_to_assign', self.color_to_assign)

    @api.multi
    def set_color_payment_pending(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_payment_pending', self.color_payment_pending)

    @api.multi
    def set_color_letter_pre_reservation(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_letter_pre_reservation', self.color_letter_pre_reservation)

    @api.multi
    def set_color_letter_reservation(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_letter_reservation', self.color_letter_reservation)

    @api.multi
    def set_color_letter_reservation_pay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_letter_reservation_pay', self.color_letter_reservation_pay)

    @api.multi
    def set_color_letter_stay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_stay', self.color_letter_stay)

    @api.multi
    def set_color_letter_stay_pay(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_letter_stay_pay', self.color_stay_pay)

    @api.multi
    def set_color_letter_checkout(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_letter_checkout', self.color_letter_checkout)

    @api.multi
    def set_color_letter_dontsell(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_letter_dontsell', self.color_letter_dontsell)

    @api.multi
    def set_color_letter_staff(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_letter_staff', self.color_letter_staff)

    @api.multi
    def set_color_letter_to_assign(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings', 'color_letter_to_assign', self.color_letter_to_assign)

    @api.multi
    def set_color_letter_payment_pending(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'color_letter_payment_pending', self.color_letter_payment_pending)

    @api.multi
    def set_default_arrival_hour(self):
        return self.env['ir.values'].sudo().set_default(
            'hotel.config.settings',
            'default_arrival_hour', self.default_arrival_hour)

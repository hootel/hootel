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


class HotelConfiguration(models.TransientModel):
    _inherit = 'hotel.config.settings'

    divide_rooms_by_capacity = fields.Boolean('Divide rooms by capacity')
    end_day_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='End day of week', default='6')
    type_move = fields.Selection([
        ('normal', 'Normal'),
        ('assisted', 'Assisted'),
        ('allow_invalid', 'Allow Invalid')
    ], string='Reservation move mode', default='normal')
    default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month')
    color_pre_reservation = fields.Char('Pre-reservation', default='#A4A4A4')
    color_reservation = fields.Char('Confirmed Reservation ', default='#4E9DC4')
    color_reservation_pay = fields.Char('Paid Reservation', default='#66CCFF')
    color_stay = fields.Char('Checkin', default='#b40606')
    color_stay_pay = fields.Char('Paid Checkin', default='#54d12b')
    color_checkout = fields.Char('Checkout', default='#FF0000')
    color_checkout_pay = fields.Char('Paid Checkout', default='#66FF33')
    color_dontsell = fields.Char('Dont Sell', default='#000000')
    color_staff = fields.Char('Staff', default='#FF9933')
    color_to_assign = fields.Char('Ota Reservation to Assign', default='#DFFF00')
    color_payment_pending = fields.Char('Payment Pending', default='#f70f0f')

    @api.multi
    def set_parity_pricelist_id(self):
        pricelist_id = super(HotelConfiguration, self).set_parity_pricelist_id()
        self.env['virtual.room.pricelist.cached'].search([]).unlink()

        pricelist_items = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist_id)])
        vroom_obj = self.env['hotel.virtual.room']
        for pitem in pricelist_items:
            date_start = pitem.date_start
            product_tmpl_id = pitem.product_tmpl_id.id
            fixed_price = pitem.fixed_price
            vroom = vroom_obj.search([
                ('product_id.product_tmpl_id', '=', product_tmpl_id),
                ('date_start', '>=', fields.datetime.now())
            ], limit=1)
            vroom_pr_cached_obj.create({
                'virtual_room_id': vroom.id,
                'date': date_start,
                'price': prod_price,
            })

        return pricelist_id

    @api.multi
    def set_color_pre_reservation(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_pre_reservation', self.color_pre_reservation)

    @api.multi
    def set_color_reservation(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_reservation', self.color_reservation)

    @api.multi
    def set_color_reservation_pay(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_reservation_pay', self.color_reservation_pay)

    @api.multi
    def set_color_stay(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_stay', self.color_stay)

    @api.multi
    def set_color_stay_pay(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_stay_pay', self.color_stay_pay)

    @api.multi
    def set_color_checkout(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_checkout', self.color_checkout)

    @api.multi
    def set_color_checkout_pay(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_checkout_pay', self.color_checkout_pay)

    @api.multi
    def set_color_dontsell(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_dontsell', self.color_dontsell)

    @api.multi
    def set_color_staff(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_staff', self.color_staff)

    @api.multi
    def set_to_assign(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_to_assign', self.color_to_assign)

    @api.multi
    def set_color_payment_pending(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'color_payment_pending', self.color_payment_pending)

    @api.multi
    def set_default_arrival_hour(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_arrival_hour', self.default_arrival_hour)

    @api.multi
    def set_divide_rooms_by_capacity(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'divide_rooms_by_capacity', self.divide_rooms_by_capacity)

    @api.multi
    def set_end_day_week(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'end_day_week', self.end_day_week)

    @api.multi
    def set_type_move(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'type_move', self.type_move)

    @api.multi
    def set_default_num_days(self):
        return self.env['ir.values'].sudo().set_default('hotel.config.settings', 'default_num_days', self.default_num_days)

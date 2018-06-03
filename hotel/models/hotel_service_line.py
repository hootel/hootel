# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------
import time
import datetime
import logging
from openerp import models, fields, api, _
from openerp.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.hotel import date_utils
_logger = logging.getLogger(__name__)


class HotelServiceLine(models.Model):

    @api.one
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        line_id = self.service_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._amount_line(field_name, arg)
        return x

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._number_packages(field_name, arg)
        return x

    @api.model
    def _service_checkin(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _service_checkout(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_ser_room_line(self):
        if 'room_lines' in self.env.context and self.env.context['room_lines']:
            ids = [item[1] for item in self.env.context['room_lines']]
            return self.env['hotel.reservation'].search([('id', 'in', ids)],
                                                        limit=1)
        return False

    _name = 'hotel.service.line'
    _description = 'hotel Service line'

    service_line_id = fields.Many2one('sale.order.line', 'Service Line',
                                      required=True, delegate=True,
                                      ondelete='cascade')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web','Web')], 'Sales Channel')
    folio_id = fields.Many2one('hotel.folio', 'Folio', ondelete='cascade')
    ser_checkin = fields.Datetime('From Date', required=True,
                                       default=_service_checkin)
    ser_checkout = fields.Datetime('To Date', required=True,
                                        default=_service_checkout)
    ser_room_line = fields.Many2one('hotel.reservation','Room', default=_default_ser_room_line)

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel service line.
        """
        if 'folio_id' in vals:
            folio = self.env['hotel.folio'].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            vals.update({'channel_type': 'call'})
        return super(HotelServiceLine, self).create(vals)

    # ~ @api.multi
    # ~ def unlink(self):
    #     ~ """
    #     ~ Overrides orm unlink method.
    #     ~ @param self: The object pointer
    #     ~ @return: True/False.
    #     ~ """
    #     ~ s_line_obj = self.env['sale.order.line']
    #     ~ for line in self:
    #         ~ if line.service_line_id:
    #             ~ sale_unlink_obj = s_line_obj.browse([line.service_line_id.id])
    #             ~ sale_unlink_obj.unlink()
    #     ~ return super(HotelServiceLine, self).unlink()

    @api.onchange('product_id')
    def product_id_change_hotel(self):
        '''
            @param self: object pointer
        '''
        if self.product_id:
            if not (self.folio_id and self.folio_id.partner_id) and \
                    self.ser_room_line:
                self.folio_id = self.ser_room_line.folio_id

            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
            self.product_uom = self.product_id.uom_id
            self.price_unit = self.product_id.price

            self.tax_id = [(6, False, self.product_id.taxes_id.ids)]
                #~ self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                                  #~ prod.taxes_id,
                                                                  #~ self.tax_id)

    #     ~ _logger.info(self._context)
    #     ~ if 'folio_id' in self._context:
    #         ~ _logger.info(self._context)
    #         ~ domain_rooms = []
    #         ~ rooms_lines = self.env['hotel.reservation'].search([('folio_id','=',folio_id)])
    #         ~ room_ids = room_lines.mapped('id')
    #         ~ domain_rooms.append(('id','in',room_ids))
    #         ~ return {'domain': {'ser_room_line': domain_rooms}}
    #
    # ~ @api.onchange('folio_id')
    # ~ def folio_id_change(self):
    #     ~ self.ensure_one()
    #     ~ _logger.info(self.mapped('folio_id.room_lines'))
    #     ~ rooms = self.mapped('folio_id.room_lines.id')
    #     ~ return {'domain': {'ser_room_line': rooms}}

    #~ @api.onchange('product_uom')
    #~ def product_uom_change(self):
        #~ '''
        #~ @param self: object pointer
        #~ '''
        # ~ if not self.product_uom:
        #     ~ self.price_unit = 0.0
        #     ~ return
        # ~ self.price_unit = self.product_id.lst_price
        # ~ if self.folio_id.partner_id:
        #     ~ prod = self.product_id.with_context(
        #         ~ lang=self.folio_id.partner_id.lang,
        #         ~ partner=self.folio_id.partner_id.id,
        #         ~ quantity=1,
        #         ~ date_order=self.folio_id.date_order,
        #         ~ pricelist=self.folio_id.pricelist_id.id,
        #         ~ uom=self.product_uom.id
        #     ~ )
        #     ~ tax_obj = self.env['account.tax']
        #     ~ self.price_unit = tax_obj._fix_tax_included_price(prod.price,
        #                                                       ~ prod.taxes_id,
        #                                                       ~ self.tax_id)

    @api.onchange('ser_checkin', 'ser_checkout')
    def on_change_checkout(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        now_utc_dt = date_utils.now()
        if not self.ser_checkin:
            self.ser_checkin = now_utc_dt.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.ser_checkout:
            self.ser_checkout = now_utc_dt.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)
        chkin_utc_dt = date_utils.get_datetime(self.ser_checkin)
        chkout_utc_dt = date_utils.get_datetime(self.ser_checkout)
        if chkout_utc_dt < chkin_utc_dt:
            raise UserError(_('Checkout must be greater or equal checkin date'))
        if self.ser_checkin and self.ser_checkout:
            diffDate = date_utils.date_diff(self.ser_checkin,
                                            self.ser_checkout, hours=False) + 1
            self.product_uom_qty = diffDate + 1

    @api.multi
    def button_confirm(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_confirm()
        return x

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_done()
        return x

    @api.one
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        sale_line_obj = self.env['sale.order.line'
                                 ].browse(self.service_line_id.id)
        return sale_line_obj.copy_data(default=default)

    @api.multi
    def unlink(self):
        for record in self:
            record.service_line_id.unlink()
        return super(HotelServiceLine, self).unlink()

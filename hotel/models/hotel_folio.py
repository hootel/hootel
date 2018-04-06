# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Dario Lodeiros <>
#                       Alexandre Díaz <dev@redneboa.es>
#                       SerpentCS
#
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
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import (
    misc,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from openerp import models, fields, api, _
from openerp import workflow
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from odoo.addons.hotel import date_utils
import datetime
import time
import pytz
import logging
_logger = logging.getLogger(__name__)


class HotelFolio(models.Model):

    @api.multi
    def name_get(self):
        res = []
        disp = ''
        for rec in self:
            if rec.order_id:
                disp = str(rec.name)
                res.append((rec.id, disp))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        args += ([('name', operator, name)])
        mids = self.search(args, limit=100)
        return mids.name_get()

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state folio on the menu badge.
         @param self: object pointer
        """
        return self.search_count([('state', '=', 'draft')])

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelFolio, self).copy(default=default)

    @api.multi
    def _invoiced(self, name, arg):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced(name, arg)

    @api.multi
    def _invoiced_search(self, obj, name, args):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced_search(obj, name, args)

    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _rec_name = 'order_id'
    _order = 'id'
    _inherit = ['ir.needaction_mixin', 'mail.thread']

    name = fields.Char('Folio Number', readonly=True, index=True,
                       default='New')
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    image = fields.Binary('Image', related='partner_id.image')
    order_id = fields.Many2one('sale.order', 'Order', delegate=True,
                               required=True, ondelete='cascade')

    room_lines = fields.One2many('hotel.reservation', 'folio_id',
                                 readonly=False,
                                 states={'done': [('readonly', True)]},
                                 help="Hotel room reservation detail.",
                                 track_visibility='always')
    service_lines = fields.One2many('hotel.service.line', 'folio_id',
                                    readonly=False,
                                    states={'done': [('readonly', True)]},
                                    help="Hotel services detail provide to"
                                    "customer and it will include in "
                                    "main Invoice.",
                                    track_visibility='always')
    hotel_policy = fields.Selection([('prepaid', 'On Booking'),
                                     ('manual', 'On Check In'),
                                     ('picking', 'On Checkout')],
                                    'Hotel Policy', default='manual',
                                    help="Hotel policy for payment that "
                                    "either the guest has to payment at "
                                    "booking time or check-in "
                                    "check-out time.")
    duration = fields.Float('Duration in Days',
                            help="Number of days which will automatically "
                            "count from the check-in and check-out date. ")
    currrency_ids = fields.One2many('currency.exchange', 'folio_no',
                                    readonly=True)
    #~ partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=False, required=True, help="Invoice address for current sales order.")
    hotel_invoice_id = fields.Many2one('account.invoice', 'Invoice')
    invoices_amount = fields.Monetary(compute='compute_invoices_amount',
                                      store=True)
    refund_amount = fields.Monetary(compute='compute_invoices_amount',
                                    store=True)
    invoices_paid = fields.Monetary(compute='compute_invoices_amount',
                                    store=True)
    booking_pending = fields.Integer('Booking pending',
                                     compute='_compute_cardex_count')
    cardex_count = fields.Integer('Cardex counter',
                                  compute='_compute_cardex_count')
    cardex_pending = fields.Boolean('Cardex Pending',
                                    compute='_compute_cardex_count')
    cardex_pending_num = fields.Integer('Cardex Pending',
                                        compute='_compute_cardex_count')
    checkins_reservations = fields.Integer('checkins reservations')
    checkouts_reservations = fields.Integer('checkouts reservations')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')
    cancelled_reason = fields.Text('Cause of cancelled')
    prepaid_warning_days = fields.Integer(
        'Prepaid Warning Days',
        help='Margin in days to create a notice if a payment \
                advance has not been recorded')
    color = fields.Char(string='Color')
    reservation_type = fields.Selection([
        ('normal', 'Normal'),
        ('staff', 'Staff'),
        ('out', 'Out of Service')], 'Type',
        default=lambda *a: 'normal')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('web','Web'),], 'Sales Channel')

    @api.model
    def daily_plan(self):
        _logger.info('daily_plan')
        self._cr.execute("update hotel_folio set checkins_reservations = 0, \
            checkouts_reservations = 0 where checkins_reservations > 0  \
            or checkouts_reservations > 0")
        folios_in = self.env['hotel.folio'].search([
            ('room_lines.is_checkin', '=', True)
        ])
        folios_out = self.env['hotel.folio'].search([
            ('room_lines.is_checkout', '=', True)
        ])
        for fol in folios_in:
            count_checkin = fol.room_lines.search_count([
                ('is_checkin', '=', True), ('folio_id.id', '=', fol.id)
            ])
            fol.write({'checkins_reservations': count_checkin})
        for fol in folios_out:
            count_checkout = fol.room_lines.search_count([
                ('is_checkout', '=', True),
                ('folio_id.id', '=', fol.id)
            ])
            fol.write({'checkouts_reservations': count_checkout})
        return True

    @api.depends('amount_total', 'room_lines', 'service_lines')
    @api.multi
    def compute_invoices_amount(self):
        _logger.info('compute_invoices_amount')
        acc_pay_obj = self.env['account.payment']
        for record in self:
            total_inv_refund = 0
            payments = acc_pay_obj.search([
                '|',
                ('invoice_ids', 'in', record.invoice_ids.ids),
                ('folio_id', '=', record.id)
            ])
            total_paid = sum(pay.amount for pay in payments)
            for inv in record.invoice_ids:
                if inv.type == 'out_refund':
                    total_inv_refund += inv.amount_total
            vals = {
                'invoices_amount': record.amount_total - total_paid,
                'invoices_paid': total_paid,
                'refund_amount': total_inv_refund,
            }
            record.update(vals)

    @api.multi
    def action_pay(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.invoices_amount
        view_id = self.env.ref('hotel.view_account_payment_folio_form').id
        return{
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': {
                'default_folio_id': self.id,
                'default_amount': amount,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': partner,
                'default_communication': self.name,
            },
            'target': 'new',
        }

    @api.multi
    def action_payments(self):
        self.ensure_one()
        payments_obj = self.env['account.payment']
        payments = payments_obj.search([('folio_id','=',self.id)])
        payment_ids = payments.mapped('id')
        invoices = self.mapped('invoice_ids.id')
        return{
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', payment_ids)],
        }

    @api.multi
    def action_refunds_invoices(self):
        self.ensure_one()
        invoices = self.mapped('invoice_ids.id')
        return{
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoices), ('type', '=', 'out_refund')],
        }

    @api.multi
    def action_checks(self):
        self.ensure_one()
        rooms = self.mapped('room_lines.id')
        return {
            'name': _('Cardexs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cardex',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', 'in', rooms)],
            'target': 'new',
        }

    @api.multi
    def action_folios_amount(self):
        now_utc_dt = date_utils.now()
        now_utc_str = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        reservations = self.env['hotel.reservation'].search([
            ('checkout', '<=', now_utc_str)
        ])
        folio_ids = reservations.mapped('folio_id.id')
        folios = self.env['hotel.folio'].search([('id', 'in', folio_ids)])
        folios = folios.filtered(lambda r: r.invoices_amount > 0)
        return {
            'name': _('Pending'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.folio',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', folios.ids)]
        }

    @api.multi
    def _compute_cardex_count(self):
        _logger.info('_compute_cardex_amount')
        for fol in self:
            num_cardex = 0
            pending = False
            if fol.reservation_type == 'normal':
                for reser in fol.room_lines:
                    if reser.state != 'cancelled':
                        num_cardex += len(reser.cardex_ids)
                fol.cardex_count = num_cardex
                pending = 0
                for reser in fol.room_lines:
                    if reser.state != 'cancelled':
                        pending += (reser.adults + reser.children) \
                                          - len(reser.cardex_ids)
                if pending <= 0:
                    fol.cardex_pending = False
                else:
                    fol.cardex_pending = True
        fol.cardex_pending_num = pending

    @api.multi
    def go_to_currency_exchange(self):
        '''
         when Money Exchange button is clicked then this method is called.
        -------------------------------------------------------------------
        @param self: object pointer
        '''
        cr, uid, context = self.env.args
        context = dict(context)
        for rec in self:
            if rec.partner_id.id and len(rec.room_lines) != 0:
                context.update({'folioid': rec.id, 'guest': rec.partner_id.id,
                                'room_no': rec.room_lines[0].product_id.name})
                self.env.args = cr, uid, misc.frozendict(context)
            else:
                raise except_orm(_('Warning'), _('Please Reserve Any Room.'))
        return {'name': _('Currency Exchange'),
                'res_model': 'currency.exchange',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'form,tree',
                'view_type': 'form',
                'context': {'default_folio_no': context.get('folioid'),
                            'default_hotel_id': context.get('hotel'),
                            'default_guest_name': context.get('guest'),
                            'default_room_number': context.get('room_no')
                            },
                }

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        _logger.info('create')
        if not 'service_lines' and 'folio_id' in vals:
            tmp_room_lines = vals.get('room_lines', [])
            vals['order_policy'] = vals.get('hotel_policy', 'manual')
            vals.update({'room_lines': []})
            for line in (tmp_room_lines):
                line[2].update({'folio_id': folio_id})
            vals.update({'room_lines': tmp_room_lines})
            folio_id = super(HotelFolio, self).create(vals)
        else:
            if not vals:
                vals = {}
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.folio')
            folio_id = super(HotelFolio, self).create(vals)

        return folio_id


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('onchange_partner_id')
        if self.partner_id:
            partner_rec = self.env['res.partner'].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise UserError(_('Not Any Order For  %s ') % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id
            for line in self.room_lines:
                _logger.info(line.id)
                days_diff = date_utils.date_diff(line.checkin,
                                                 line.checkout,
                                                 hours=False) + 1
                res = line.prepare_reservation_lines(line.checkin, days_diff)
                line.reservation_lines = res['commands']
                line.price_unit = res['total_price']
        self.currency_id = self.env.ref('base.main_company').currency_id
        """
        Warning messajes saved in partner form to folios
        """
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id \
                    and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            title = _("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if self.partner_id.sale_warn == 'block':
                self.update({
                    'partner_id': False,
                    'partner_invoice_id': False,
                    'partner_shipping_id': False,
                    'pricelist_id': False
                })
                return {'warning': warning}

        if warning:
            return {'warning': warning}

    @api.multi
    def button_dummy(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            folio.order_id.button_dummy()
        return True

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        for line in self.room_lines:
            if line.state == "booking":
                line.action_reservation_checkout()

    @api.multi
    def action_invoice_create(self, grouped=False, states=None):
        '''
        @param self: object pointer
        '''
        if states is None:
            states = ['confirmed', 'done']
        order_ids = [folio.order_id.id for folio in self]
        room_lst = []
        sale_obj = self.env['sale.order'].browse(order_ids)
        invoice_id = (sale_obj.action_invoice_create(grouped=False,
                                                     states=['confirmed',
                                                             'done']))
        for line in self:
            values = {'invoiced': True,
                      'state': 'progress' if grouped else 'progress',
                      'hotel_invoice_id': invoice_id
                      }
            line.write(values)
            for rec in line.room_lines:
                room_lst.append(rec.product_id)
            for room in room_lst:
                room_obj = self.env['hotel.room'].search([
                    ('name', '=', room.name)
                ])
        return invoice_id

    @api.multi
    def action_invoice_cancel(self):
        '''
        @param self: object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        res = sale_obj.action_invoice_cancel()
        for sale in self:
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
            sale.write({'state': 'invoice_except'})
        return res

    @api.multi
    def action_cancel(self):
        '''
        @param self: object pointer
        '''
        for sale in self:
            if not sale.order_id:
                raise ValidationError(_('Order id is not available'))
            for invoice in sale.invoice_ids:
                invoice.state = 'cancel'
            sale.room_lines.action_cancel()
            sale.order_id.action_cancel()

    @api.multi
    def action_confirm(self):
        _logger.info('action_confirm')
        auto_done = self.env['ir.values'].get_default('sale.config.settings',
                                                      'auto_done_setting')

        for sale in self:
            for order in sale.order_id:
                order.state = 'sale'
                order.order_line._action_procurement_create()
                if not order.project_id:
                    for line in order.order_line:
                        if line.product_id.invoice_policy == 'cost':
                            order._create_analytic_account()
                            break
            sale.room_lines.confirm()
            if auto_done:
                sale.order_id.action_done()

    @api.multi
    def print_quotation(self):
        self.order_id.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self.order_id, 'sale.report_saleorder')

    @api.multi
    def action_cancel_draft(self):
        '''
        @param self: object pointer
        '''
        if not len(self._ids):
            return False
        for room in self.room_lines:
            room.state = 'draft'
        query = "select id from sale_order_line \
        where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(self._ids), 'cancel'))
        cr1 = self._cr
        line_ids = map(lambda x: x[0], cr1.fetchall())
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        sale_line_obj = self.env['sale.order.line'].browse(line_ids)
        sale_line_obj.write({'invoiced': False, 'state': 'draft',
                             'invoice_lines': [(6, 0, [])]})
        return True

    @api.multi
    def send_reservation_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel',
                            'mail_template_hotel_reservation')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.multi
    def send_cancel_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel',
                            'mail_template_hotel_cancel')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(dt)
        now_date = datetime.strptime(now_str, dt)
        ir_model_data = self.env['ir.model.data']
        template_id = (ir_model_data.get_object_reference
                       ('hotel_reservation',
                        'mail_template_reservation_reminder_24hrs')[1])
        template_rec = self.env['mail.template'].browse(template_id)
        for reserv_rec in self.search([]):
            checkin_date = (datetime.strptime(reserv_rec.checkin, dt))
            difference = relativedelta(now_date, checkin_date)
            if(difference.days == -1 and reserv_rec.partner_id.email and
               reserv_rec.state == 'confirm'):
                template_rec.send_mail(reserv_rec.id, force_send=True)
        return True

    @api.multi
    def unlink(self):
        for record in self:
            record.order_id.unlink()
        return super(HotelFolio, self).unlink()

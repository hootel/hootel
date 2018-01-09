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
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import misc, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import pytz
import time
import logging
_logger = logging.getLogger(__name__)

def _offset_format_timestamp1(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, context=None):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the
    correct offset if both the server and local timeZone are recognized,or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they
    are both in the same TZ).
    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    dst_tz = pytz.timezone('UTC')
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res

class HotelReservation(models.Model):

    @api.depends('state', 'reservation_type', 'folio_id.invoices_amount')
    def _compute_color(self):
        now_str = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for rec in self:
            now_date = datetime.strptime(now_str,DEFAULT_SERVER_DATETIME_FORMAT)
            checkin_date = (datetime.strptime(
                                rec.checkin,
                                DEFAULT_SERVER_DATETIME_FORMAT))
            difference_checkin = relativedelta(now_date, checkin_date)
            checkout_date = (datetime.strptime(
                                rec.checkout,
                                DEFAULT_SERVER_DATETIME_FORMAT))
            difference_checkout = relativedelta(now_date, checkout_date)
            if rec.reservation_type == 'staff':
                rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_staff')
            elif rec.reservation_type == 'out':
                rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_dontsell')
            elif rec.to_assign == True:
                rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_to_assign')
            elif rec.state == 'draft':
                rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_pre_reservation')
            elif rec.state == 'confirm':
                if rec.folio_id.invoices_amount == 0:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_reservation_pay')
                else:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_reservation')
            elif rec.state == 'booking' and difference_checkout.days == 0:
                if rec.folio_id.invoices_amount == 0:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_checkout_pay')
                else:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_checkout')
            elif rec.state == 'booking':
                if rec.folio_id.invoices_amount == 0:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_stay_pay')
                else:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_stay')
            else:
                if rec.folio_id.invoices_amount == 0:
                    rec.reserve_color = '#FFFFFF'
                else:
                    rec.reserve_color = self.env['ir.values'].get_default('hotel.config.settings', 'color_payment_pending')
            rec.write({}) #To dispatch the calendar bus notification
            rec.folio_id.color = rec.reserve_color
            return rec.reserve_color


    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''

        return super(HotelReservation, self).copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._amount_line(field_name, arg)

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._number_packages(field_name, arg)

    @api.multi
    def _get_default_checkin(self):
        folio = False
        default_arrival_hour = self.env['ir.values'].get_default('hotel.config.settings', 'default_arrival_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([('id','=', self._context['folio_id'])])
        if folio and folio.room_lines:
            return folio.room_lines[0].checkin
        else:
            from_zone = self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel')
            return datetime.strptime(_offset_format_timestamp1(time.strftime("%Y-%m-%d {0}".format(default_arrival_hour)),
                                             '%Y-%m-%d %H:%M',
                                             '%Y-%m-%d %H:%M',
                                             ignore_unparsable_time=True,
                                             context={'tz': from_zone}),
                                             '%Y-%m-%d %H:%M')

    @api.model
    def _get_default_checkout(self):
        folio = False
        default_departure_hour = self.env['ir.values'].get_default('hotel.config.settings', 'default_departure_hour')
        if 'folio_id' in self._context:
            folio = self.env['hotel.folio'].search([('id','=',self._context['folio_id'])])
        if folio and folio.room_lines:
                        return folio.room_lines[0].checkout
        else:
            from_zone = self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel')
            tm_delta = timedelta(days=1)
            return datetime.strptime(_offset_format_timestamp1
                                      (time.strftime("%Y-%m-%d {0}".format(default_departure_hour)),
                                       '%Y-%m-%d %H:%M',
                                       '%Y-%m-%d %H:%M',
                                       ignore_unparsable_time=True,
                                       context={'tz': from_zone}),
                                      '%Y-%m-%d %H:%M') + tm_delta

    @api.model
    def name_search(self,name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += ['|',
                ('folio_id.name', operator, name),
                ('product_id.name', operator, name)
                ]
        return super(HotelReservation, self).name_search(
            name='', args = args, operator = 'ilike',
            limit = limit)


    @api.multi
    def name_get(self):
        result=[]
        for res in self:
            name = u'%s (%s)' % (res.folio_id.name,
                            res.product_id.name)
            result.append((res.id, name))
        return result

    _name = 'hotel.reservation'
    _description = 'hotel reservation'
    _inherit = ['ir.needaction_mixin','mail.thread']

    _defaults = {
        'product_id': False
    }

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    adults = fields.Integer('Adults', size=64, readonly=True,
                            states={'draft': [('readonly', False)]},
                            track_visibility='always',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children', size=64, readonly=True,
                              states={'draft': [('readonly', False)]},
                              track_visibility='always',
                              help='Number of children there in guest list.')
    to_assign = fields.Boolean('To Assign')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('booking', 'Booking'), ('done', 'Done'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='always')
    reservation_type = fields.Selection([
                                ('normal', 'Normal'),
                                ('staff', 'Staff'),
                                ('out', 'Out of Service')
                                ], 'Reservation Type', default=lambda *a: 'normal')
    cancelled_reason = fields.Text('Cause of cancelled')
    out_service_description = fields.Text('Cause of out of service')
    order_line_id = fields.Many2one('sale.order.line', string='Order Line',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', string='Folio',
                               ondelete='cascade')
    checkin = fields.Datetime('Check In', required=True,
                                   default=_get_default_checkin,
                                   track_visibility='always')
    checkout = fields.Datetime('Check Out', required=True,
                                    default=_get_default_checkout,
                                    track_visibility='always')
    room_type_id = fields.Many2one('hotel.room.type',string='Room Type')
    virtual_room_id = fields.Many2one('hotel.virtual.room',string='Virtual Room Type')
    partner_id = fields.Many2one (related='folio_id.partner_id')
    reservation_lines = fields.One2many('hotel.reservation.line',
                                        'reservation_id',
                                        readonly=True,
                                        states={'draft': [('readonly', False)],
                                                'sent': [('readonly', False)]})
    reserve_color = fields.Char(compute='_compute_color',string='Color', store=True)
    service_line_ids = fields.One2many('hotel.service.line','ser_room_line')
    pricelist_id = fields.Many2one('product.pricelist',related='folio_id.pricelist_id',readonly="1")
    cardex_ids = fields.One2many('cardex', 'reservation_id')
    cardex_count = fields.Integer('Cardex counter', compute='_compute_cardex_count')
    cardex_pending = fields.Boolean('Cardex Pending', compute='_compute_cardex_count')
    cardex_pending_num = fields.Integer('Cardex Pending Num', compute='_compute_cardex_count')
    check_rooms = fields.Boolean('Check Rooms')
    is_checkin = fields.Boolean()
    is_checkout = fields.Boolean()
    splitted = fields.Boolean('Splitted', default=False)
    parent_reservation = fields.Many2one('hotel.reservation', 'Parent Reservation')

    @api.multi
    def _compute_cardex_count(self):
        for res in self:
            res.cardex_count = len(res.cardex_ids)
            res.cardex_pending_num = res.adults + res.children - len(res.cardex_ids)
            if (res.adults + res.children - len(res.cardex_ids))<=0:
                res.cardex_pending = False
            else:
                res.cardex_pending = True

    @api.model
    def daily_plan(self):
        today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        yesterday = (date.today() - timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        reservations = self.env['hotel.reservation'].search([('reservation_lines.date','in',[today,yesterday]),('state','in',['confirm','booking'])])
        self._cr.execute("update hotel_reservation set is_checkin = False, is_checkout = False where is_checkin = True or is_checkout = True")
        checkins_res = reservations.filtered(lambda x: (
            x.state == 'confirm' and x.checkin[0:10] == today and x.reservation_type == 'normal'))
        checkins_res.write({'is_checkin':True})
        checkouts_res = reservations.filtered(lambda x: (
            x.state == 'booking' and x.checkout[0:10] == today and x.reservation_type == 'normal'))
        checkouts_res.write({'is_checkout':True})
        self.env['hotel.folio'].daily_plan()
        return True

    @api.model
    def checkin_is_today(self):
        self.ensure_one()
        tz_hotel = pytz.timezone(self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel'))
        checkin_utc_dt = datetime.strptime(self.checkin, DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_dt = checkin_utc_dt.replace(tzinfo=pytz.utc).astimezone(tz_hotel)

        date_str = checkin_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        today = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        if date_str == today:
            return True
        return False

    @api.model
    def checkout_is_today(self):
        self.ensure_one()
        tz_hotel = pytz.timezone(self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel'))
        checkout_utc_dt = datetime.strptime(self.checkout, DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_dt = checkout_utc_dt.replace(tzinfo=pytz.utc).astimezone(tz_hotel)

        date_str = checkout_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        today = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        if date_str == today:
            return True
        return False

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled',
                'to_assign': False,
                'discount': 100.0,
            })
            if record.checkin_is_today:
                record.is_checkin = False
                folio = self.env['hotel.folio'].browse(record.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([('folio_id','=',folio.id),('is_checkin','=',True)])

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|',('parent_reservation', '=', master_reservation.id),('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'cancelled')
                ])
                splitted_reservs.action_cancel()

    @api.multi
    def draft(self):
        for record in self:
            record.write({'state': 'draft','to_assign':False})

            if record.splitted:
                master_reservation = record.parent_reservation or record
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|',('parent_reservation', '=', master_reservation.id),('id', '=', master_reservation.id),
                    ('folio_id', '=', record.folio_id.id),
                    ('id', '!=', record.id),
                    ('state', '!=', 'draft')
                ])
                splitted_reservs.draft()

    @api.multi
    def action_reservation_checkout(self):
        for record in self:
            record.state = 'done'
            record.to_assign = False
            if record.checkout_is_today():
                record.is_checkout = False
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkouts_reservations = folio.room_lines.search_count([('folio_id','=',folio.id),('is_checkout','=',True)])

    @api.multi
    def unify(self):
        self.ensure_one()
        if not self.splitted or self.state == 'cancelled' or self.state == 'confirm':
            raise ValidationError("This reservation can't be unified")

        master_reservation = self.parent_reservation or self

        splitted_reservs = self.env['hotel.reservation'].search([
            ('splitted', '=', True),
            ('parent_reservation', '=', master_reservation.id),
            ('folio_id', '=', self.folio_id.id),
        ])

        rooms_products = splitted_reservs.mapped('product_id.id')
        if len(rooms_products) > 1 or (len(rooms_products) == 1 and master_reservation.product_id.id != rooms_products[0]):
            raise ValidationError("This reservation can't be unified: They all need to be in the same room")

        # Search checkout
        last_checkout = splitted_reservs[0].checkout
        for reserv in splitted_reservs:
            if last_checkout > reserv.checkout:
                last_checkout = reserv.checkout

        # Agrupate reservation lines
        reservation_lines = splitted_reservs.mapped('reservation_lines')
        reservation_lines.sorted(key=lambda r: r.date)
        rlines = []
        for rline in reservation_lines:
            rlines.append((0, False, {
                'date': rline.date,
                'price': rline.price,
            }))
        # Unify
        splitted_reservs.unlink()
        master_reservation.write({
            'reservation_lines': rlines,
            'checkout': last_checkout,
            'splitted': False,
        })

        return True

    @api.multi
    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        return {
            'name': self.name,
            'adults': self.adults,
            'children': self.children,
            'checkin': checkin or self.checkin,
            'checkout': checkout or self.checkout,
            'folio_id': self.folio_id.id,
            'product_id': self.product_id.id,
            'parent_reservation': self.parent_reservation.id,
        }


    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        record = super(HotelReservation, self).create(vals)
        if record.adults == 0:
            room = self.env['hotel.room'].search([('product_id','=',record.product_id.id)])
            record.adults = room.capacity
        return record

    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            line.uos_change(product_uos, product_uos_qty=0,
                            product_id=None)
        return True

    @api.onchange('checkin', 'checkout', 'product_id','reservation_type')
    def on_change_checkin_checkout_product_id(self):
        if not self.checkin:
            self.checkin = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            self.checkout = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.name = self.product_id.name
        self.product_uom = self.product_id.uom_id
        # UTC -> Hotel tz
        tz = self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel')
        chkin_utc_dt = fields.Datetime.from_string(self.checkin)
        chkin_dt = chkin_utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz))
        if self.checkin >= self.checkout:
            dpt_hour = self.env['ir.values'].get_default('hotel.config.settings', 'default_departure_hour')
            checkout_str = (chkin_dt + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            checkout_str = "%s %s" % (checkout_str, dpt_hour)
            self.checkout= _offset_format_timestamp1(checkout_str,
                                             '%Y-%m-%d %H:%M',
                                             '%Y-%m-%d %H:%M:%S',
                                             ignore_unparsable_time=True,
                                             context={'tz': tz})
        chkout_dt = fields.Datetime.from_string(self.checkout)
        chkout_dt = chkout_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(tz))
        days_diff = abs((chkout_dt.replace(hour=0, minute=0, second=0)  - chkin_dt.replace(hour=0, minute=0, second=0)).days-1)
        res = self.prepare_reservation_lines(chkin_dt, days_diff)
        self.reservation_lines = res['commands']

        if self.state == 'confirm' and self.checkin_is_today() :
                self.is_checkin = True
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([('folio_id','=',folio.id),('is_checkin','=',True)])

        if self.state == 'booking' and self.checkout_is_today():
                self.is_checkout = False
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkouts_reservations = folio.room_lines.search_count([('folio_id','=',folio.id),('is_checkout','=',True)])

        if self.reservation_type in ['staff','out']:
            self.price_unit = 0.0
        else:
            self.price_unit = res['total_price']
        if self.product_id:
            room = self.env['hotel.room'].search([('product_id', '=', self.product_id.id)])
            if self.adults == 0:
                self.adults = room.capacity
            if room.price_virtual_room:
                self.virtual_room_id = room.price_virtual_room.id

    @api.multi
    def prepare_reservation_lines(self, datefrom, days):
        self.ensure_one()
        total_price = 0.0
        cmds = [(5, False, False)]

        room = self.env['hotel.room'].search([('product_id', '=', self.product_id.id)])
        product_id = room.sale_price_type == 'vroom' and room.price_virtual_room.product_id or self.product_id
        pricelist_id = self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        for i in range(0, days + 1):
            ndate = datefrom + timedelta(days=i)
            ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
            prod = product_id.with_context(
                lang=self.partner_id.lang,
                partner=self.partner_id.id,
                quantity=1,
                date=ndate_str,
                pricelist=pricelist_id,
                uom=self.product_uom.id)
            line_price = prod.price
            cmds.append((0, False, {
                'date': ndate_str,
                'price': line_price
            }))
            total_price += line_price
        if self.adults == 0 and self.product_id:
            room = self.env['hotel.room'].search([('product_id', '=', self.product_id.id)])
            self.adults = room.capacity
        return {'total_price': total_price, 'commands': cmds}


    @api.multi
    @api.onchange('checkin', 'checkout','room_type_id','virtual_room_id','check_rooms')
    def on_change_checkout(self):
        '''
        When you change checkin or checkout it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        self.ensure_one()
        now_utc_dt = fields.datetime.now()
        if not self.checkin:
            self.checkin = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout:
            now_utc_dt = self.checkin.strptime(DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=1)
            self.checkout = now_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        occupied = self.env['hotel.reservation'].occupied(self.checkin, self.checkout)
        rooms_occupied= occupied.mapped('product_id.id')
        domain_rooms = [('isroom','=',True),('id', 'not in', rooms_occupied)]
        if self.room_type_id:
            domain_rooms.append(('categ_id.id', '=', self.room_type_id.cat_id.id))
        if self.virtual_room_id:
            room_categories = self.virtual_room_id.room_type_ids.mapped('cat_id.id')
            link_virtual_rooms = self.virtual_room_id.room_ids | self.env['hotel.room'].search([('categ_id.id','in',room_categories)])
            room_ids = link_virtual_rooms.mapped('product_id.id')
            domain_rooms.append(('id','in',room_ids))
        return {'domain': {'product_id': domain_rooms}}

    @api.multi
    def confirm(self):
        '''
        @param self: object pointer
        '''
        for r in self:
            r.write({'state': 'confirm','to_assign':False})
            if r.checkin_is_today():
                r.is_checkin = True
                folio = self.env['hotel.folio'].browse(self.folio_id.id)
                folio.checkins_reservations = folio.room_lines.search_count([('folio_id','=',folio.id),('is_checkin','=',True)])

            if r.splitted:
                master_reservation = r.parent_reservation or r
                splitted_reservs = self.env['hotel.reservation'].search([
                    ('splitted', '=', True),
                    '|',('parent_reservation', '=', master_reservation.id),('id', '=', master_reservation.id),
                    ('folio_id', '=', r.folio_id.id),
                    ('id', '!=', r.id),
                    ('state', '!=', 'confirm')
                ])
                splitted_reservs.confirm()
        return True


    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        self.write({'state': 'done'})
        for folio_line in self:
            workflow.trg_write(self._uid, 'sale.order',
                               folio_line.order_line_id.order_id.id,
                               self._cr)
        return True

    @api.one
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        line_id = self.order_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)

    @api.constrains('checkin', 'checkout', 'state')
    def check_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        if self.checkin >= self.checkout:
                raise ValidationError(_('Room line Check In Date Should be \
                less than the Check Out Date!'))
        occupied = self.env['hotel.reservation'].occupied(self.checkin, self.checkout)
        occupied = occupied.filtered(lambda r: r.product_id.id == self.product_id.id and r.id != self.id)
        occupied_name = ','.join(str(x.folio_id.name) for x in occupied)
        if occupied:
           warning_msg = 'You tried to confirm \
               reservation with room those already reserved in this \
               reservation period: %s' % occupied_name
           raise ValidationError(warning_msg)

    @api.multi
    def unlink(self):
        self.order_line_id.unlink()
        return super(HotelReservation, self).unlink()

    @api.model
    def occupied(self, checkin, checkout):
        """
        Return a RESERVATIONS array between in and out parameters
        IMPORTANT: This function should receive the dates in UTC datetime zone, as String format
        """
        tz_hotel = pytz.timezone(self.env['ir.values'].get_default('hotel.config.settings', 'tz_hotel'))
        checkin_utc_dt = datetime.strptime(checkin, DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_dt = checkin_utc_dt.replace(tzinfo=pytz.utc).astimezone(tz_hotel)
        checkout_utc_dt = datetime.strptime(checkout, DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_dt = checkout_utc_dt.replace(tzinfo=pytz.utc).astimezone(tz_hotel)

        dates_str = [(checkin_dt + timedelta(days=x)).strftime(DEFAULT_SERVER_DATE_FORMAT) for x in range((checkout_dt-checkin_dt).days)]
        reservations = self.env['hotel.reservation'].search([('reservation_lines.date','in',dates_str),('state','!=','cancelled')])

        return reservations

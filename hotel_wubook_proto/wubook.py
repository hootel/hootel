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
import xmlrpclib
import re
from datetime import datetime, timedelta
from urlparse import urljoin
from openerp import models, api
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

DEFAULT_WUBOOK_DATE_FORMAT = "%d/%m/%Y"
DEFAULT_WUBOOK_TIME_FORMAT = "%H:%M"
DEFAULT_WUBOOK_DATETIME_FORMAT = "%s %s" % (DEFAULT_WUBOOK_DATE_FORMAT,
                                            DEFAULT_WUBOOK_TIME_FORMAT)
WUBOOK_STATUS_CANCELLED = 5
WUBOOK_STATUS_REFUSED = 3


def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]


class WuBook(models.TransientModel):
    _name = 'wubook'

    def __init__(self, pool, cr):
        init_res = super(WuBook, self).__init__(pool, cr)
        self.SERVER = False
        self.LCODE = False
        self.TOKEN = False
        return init_res

    def init_connection_(self):
        user_r = self.env['res.users'].browse(self.env.uid)

        user = user_r.partner_id.wubook_user
        passwd = user_r.partner_id.wubook_passwd
        self.LCODE = user_r.partner_id.wubook_lcode
        pkey = user_r.partner_id.wubook_pkey
        server_addr = user_r.partner_id.wubook_server

        self.SERVER = xmlrpclib.Server(server_addr)
        res, tok = self.SERVER.acquire_token(user, passwd, pkey)
        self.TOKEN = tok

        if res != 0:
            raise UserError("Can't connect with WuBook!")

        return True

    def close_connection_(self):
        self.SERVER.release_token(self.TOKEN)
        self.TOKEN = False
        self.SERVER = False

    @api.model
    def create_room(self, vals):
        self.init_connection_()
        shortcode = self.env['ir.sequence'].get('seq_vroom_id')
        res, rid = self.SERVER.new_room(
            self.TOKEN,
            self.LCODE,
            0,
            vals['name'],
            vals['wcapacity'],
            vals['list_price'],
            'max_real_rooms' in vals and vals['max_real_rooms'] or 1,
            shortcode[:4],
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )
        self.close_connection_()

        if res == 0:
            vals.update({'wrid': rid})
        else:
            raise UserError("Can't create room in WuBook!")
        return vals

    @api.model
    def modify_room(self, vroomid):
        self.init_connection_()
        vroom = self.env['hotel.virtual.room'].browse([vroomid])
        res, rid = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            vroom.wrid,
            vroom.name,
            vroom.wcapacity,
            vroom.list_price,
            vroom.max_real_rooms,
            vroom.wscode,
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )
        self.close_connection_()

        if res != 0:
            raise UserError("Can't modify room in WuBook!")

        return True

    @api.model
    def delete_room(self, vroomid):
        self.init_connection_()
        vroom = self.env['hotel.virtual.room'].browse([vroomid])
        res, rid = self.SERVER.del_room(
            self.TOKEN,
            self.LCODE,
            vroom.wrid
        )
        self.close_connection_()

        if res != 0:
            raise UserError("Can't delete room in WuBook!")

        return True

    @api.model
    def import_rooms(self):
        self.init_connection_()
        res, rooms = self.SERVER.fetch_rooms(
            self.TOKEN,
            self.LCODE,
            0
        )
        self.close_connection_()

        vroom_obj = self.env['hotel.virtual.room']
        if res == 0:
            for room in rooms:
                vroom = vroom_obj.search([('wrid', '=', room['id'])], limit=1)
                vals = {
                    'name': room['name'],
                    'wrid': room['id'],
                    'wscode': room['shortname'],
                    'list_price': room['price'],
                    #'max_real_rooms': room['availability'],
                }
                if vroom:
                    vroom.with_context({'wubook_action': False}).write(vals)
                else:
                    vroom_obj.with_context({'wubook_action': False}).create(vals)
        else:
            raise UserError("Can't import rooms from WuBook!")

        return True

    @api.model
    def push_activation(self):
        errors = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url').replace("http://", "https://")

        self.init_connection_()

        res, code = self.SERVER.push_activation(self.TOKEN,
                                                self.LCODE,
                                                urljoin(base_url, "/wubook/push/reservations"),
                                                1)
        if res != 0:
            errors.append("Can't activate push reservations: %s" % code)

        res, code = self.SERVER.push_update_activation(self.TOKEN,
                                                       self.LCODE,
                                                       urljoin(base_url, "/wubook/push/rooms"))
        if res != 0:
            errors.append("Can't activate push rooms: %s" % code)

        self.close_connection_()

        if any(errors):
            raise UserError('\n'.join(errors))

        return True

    @api.model
    def corporate_fetch(self):
        self.init_connection_()
        res = self.SERVER.corporate_fetchable_properties(self.TOKEN)
        self.close_connection_()
        return True

    @api.model
    def fetch_new_bookings(self):
        self.init_connection_()
        res, bookings = self.SERVER.fetch_new_bookings(self.TOKEN,
                                                       self.LCODE,
                                                       1,
                                                       0)
        if res == 0:
            processed_rids = self.generate_reservations(bookings)
            if any(processed_rids):
                res, data = self.SERVER.mark_bookings(self.TOKEN,
                                                      self.LCODE,
                                                      processed_rids)
        self.close_connection_()

        if res != 0:
            raise ValidationError("Can't process reservations from wubook!")

        return True

    @api.model
    def fetch_booking(self, lcode, rcode):
        self.init_connection_()
        res, bookings = self.SERVER.fetch_booking(self.TOKEN,
                                                  lcode,
                                                  rcode)
        if res == 0:
            processed_rids = self.generate_reservations(bookings)
            if any(processed_rids):
                res, data = self.SERVER.mark_bookings(self.TOKEN,
                                                      lcode,
                                                      processed_rids)
        self.close_connection_()

        if res != 0:
            raise ValidationError("Can't process reservations from wubook!")

        return True

    @api.model
    def initialize(self):
        self.push_activation()
        self.import_rooms()
        #self.fetch_new_bookings()
        return True

    @api.model
    def create_reservation(self, reservid):
        self.init_connection_()
        reserv = self.env['hotel.reservation'].browse([reservid])
        vroom = self.env['hotel.virtual.room'].search([('product_id', '=', reserv.product_id.id)], limit=1)
        res, rcode = self.SERVER.new_reservation(self.TOKEN,
                                                 self.LCODE,
                                                 reserv.checkin,
                                                 reserv.checkout,
                                                 {vroom.wrid: [reserv.adults+reserv.children, 'nb']},
                                                 {
                                                    'lname': _partner_split_name(reserv.partner_id.name)[1],
                                                    'fname': _partner_split_name(reserv.partner_id.name)[0],
                                                    'email': reserv.partner_id.email,
                                                    'city': reserv.partner_id.city,
                                                    'phone': reserv.partner_id.phone,
                                                    'street': reserv.partner_id.street,
                                                    'country': reserv.partner_id.country_id.code,
                                                    'arrival_hour': datetime.strptime(reserv.checkin, "%H:%M:%S"),
                                                    'notes': '' # TODO: Falta poner el cajetin de observaciones en folio o reserva..
                                                 },
                                                 reserv.adults+reserv.children)

        self.close_connection_()
        reserv.write({'wrid': rcode})
        return True

    @api.model
    def cancel_reservation(self, reservid, reason=""):
        reserv = self.env['hotel.reservation'].browse([reservid])
        self.init_connection_()
        res, rcode = self.SERVER.cancel_reservation(self.TOKEN,
                                                    self.LCODE,
                                                    reserv.wrid,
                                                    reason)
        self.close_connection_()

        if res != 0:
            raise UserError("Can't cancel reservation in WuBook!")

        return True

    @api.model
    def generate_reservations(self, bookings):
        res_partner_obj = self.env['res.partner']
        hotel_reserv_obj = self.env['hotel.reservation']
        hotel_folio_obj = self.env['hotel.folio']
        hotel_vroom_obj = self.env['hotel.virtual.room']
        processed_rids = []
        _logger.info("GENERATE RESERVS")
        _logger.info(bookings)
        for book in bookings:
            # Already Exists?
            reservs = hotel_reserv_obj.search([('wrid', '=', str(book['reservation_code'])),
                                              ('wchannel_reservation_code', '=', str(book['channel_reservation_code']))])
            if any(reservs):
                for reserv in reservs:
                    reserv.write({
                        'wstatus': str(book['status']),
                        'wstatus_reason': book.get('status_reason', ''),
                    })

                    if book['status'] == WUBOOK_STATUS_CANCELLED \
                            or book['status'] == WUBOOK_STATUS_REFUSED:
                        reserv.action_cancel()
                continue

            # Search Customer
            country_id = self.env['res.country'].search([('name', 'ilike', book['customer_country'])], limit=1)
            customer_mail = book.get('customer_mail', False)
            partner_id = False
            if customer_mail:
                partner_id = res_partner_obj.search([('email', '=', customer_mail)], limit=1)
            if not partner_id:
                lang = self.env['res.lang'].search([('iso_code', 'ilike', book['customer_language_iso'])], limit=1)
                vals = {
                    'name': "%s %s" % (book['customer_name'], book['customer_surname']),
                    'country_id': country_id and country_id.id,
                    'city': book['customer_city'],
                    'comment': book['customer_notes'],
                    'phone': book['customer_phone'],
                    'zip': book['customer_zip'],
                    'street': book['customer_address'],
                    'email': book['customer_mail'],
                    'lang': lang and lang.id,
                    #'lang': book['customer_language']
                }
                partner_id = res_partner_obj.create(vals)

            # Obtener habitacion libre
            arr_hour = book['arrival_hour'] == "--" and '00:00' or book['arrival_hour']
            checkin = "%s %s" % (book['date_arrival'], arr_hour)
            checkin_dt = datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT)
            checkin = checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            checkout = "%s 21:59" % book['date_departure'] # FIXME: Usar UTC
            checkout_dt = datetime.strptime(checkout, DEFAULT_WUBOOK_DATETIME_FORMAT)
            checkout = checkout_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            vrooms_ids = book['rooms'].split(',')
            vrooms = hotel_vroom_obj.search([('wrid', 'in', vrooms_ids)])

            reservations = []
            for vroom in vrooms:
                free_rooms = hotel_vroom_obj.check_availability_virtual_room(checkin,
                                                                             checkout,
                                                                             vroom.id)
                if any(free_rooms):
                    # Total Price Room
                    reservation_lines = [];
                    tprice = 0.0
                    for broom in book['booked_rooms']:
                        if str(broom['room_id']) == vroom.wrid:
                            for brday in broom['roomdays']:
                                wndate = datetime.strptime(brday['day'], DEFAULT_WUBOOK_DATE_FORMAT)
                                reservation_lines.append((0, False, {
                                    'date': wndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    'price': brday['price']
                                }))
                                tprice += brday['price']
                            break
                    # Occupancy
                    occupancy = 0
                    for broom in book['rooms_occupancies']:
                        if str(broom['id']) == vroom.wrid:
                            occupancy = broom['occupancy']
                            break

                    vals = {
                        'checkin': checkin,
                        'checkout': checkout,
                        'adults': occupancy,
                        'children': 0,
                        'product_id': free_rooms[0].product_id.id,
                        'product_uom': free_rooms[0].product_id.product_tmpl_id.uom_id.id,
                        'product_uom_qty': 1,
                        'product_uos': 1,
                        'reservation_lines': reservation_lines,
                        'name': free_rooms[0].name,
                        'price_unit': tprice,
                        'to_assign': True,
                        'wrid': str(book['reservation_code']),
                        'wchannel_id': str(book['id_channel']),
                        'wchannel_reservation_code': str(book['channel_reservation_code']),
                        'wstatus': str(book['status']),
                    }
                    reservations.append((0, False, vals))
                else:
                    raise ValidationError("Can't found a free room for reservation from wubook!!!")
            # Create Folio
            vals = {'room_lines': reservations}
            hotel_folio_id = hotel_folio_obj.search([('wseed', '=', book['sessionSeed'])], limit=1)
            if hotel_folio_id and book['sessionSeed'] != '':
                hotel_folio_id.with_context({'wubook_action': False}).write(vals)
            else:
                vals.update({
                    'partner_id': partner_id.id,
                    'wseed': book['sessionSeed']
                })
                hotel_folio_id = hotel_folio_obj.with_context({'wubook_action': False}).create(vals)
            processed_rids.append(book['reservation_code'])
        return processed_rids
    
    def prepare_reservation_line_values(self, book):
        # Obtener habitacion libre
        arr_hour = book['arrival_hour'] == "--" and '00:00' or book['arrival_hour']
        checkin = "%s %s" % (book['date_arrival'], arr_hour)
        checkin_dt = datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT)
        checkin = checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        checkout = "%s 21:59" % book['date_departure'] # FIXME: Usar UTC
        checkout_dt = datetime.strptime(checkout, DEFAULT_WUBOOK_DATETIME_FORMAT)
        checkout = checkout_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        vrooms_ids = book['rooms'].split(',')
        vrooms = hotel_vroom_obj.search([('wrid', 'in', vrooms_ids)])

        reservations = []
        for vroom in vrooms:
            # Total Price Room
            reservation_lines = [];
            tprice = 0.0
            for broom in book['booked_rooms']:
                if str(broom['room_id']) == vroom.wrid:
                    for brday in broom['roomdays']:
                        wndate = datetime.strptime(brday['day'], DEFAULT_WUBOOK_DATE_FORMAT)
                        reservation_lines.append((0, False, {
                            'date': wndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            'price': brday['price']
                        }))
                        tprice += brday['price']
                    break
            # Occupancy
            occupancy = 0
            for broom in book['rooms_occupancies']:
                if str(broom['id']) == vroom.wrid:
                    occupancy = broom['occupancy']
                    break

            vals = {
                'checkin': checkin,
                'checkout': checkout,
                'adults': occupancy,
                'children': 0,
                'product_id': free_rooms[0].product_id.id,
                'product_uom': free_rooms[0].product_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': 1,
                'product_uos': 1,
                'reservation_lines': reservation_lines,
                'name': free_rooms[0].name,
                'price_unit': tprice,
                'to_assign': True,
                'wrid': str(book['reservation_code']),
                'wchannel_id': str(book['id_channel']),
                'wchannel_reservation_code': str(book['channel_reservation_code']),
                'wstatus': str(book['status']),
            }

    @api.model
    def update_availability(self, vals):
        if 'checkin' not in vals or 'checkout' not in vals or 'product_id' not in vals:
            return False

        date_start = datetime.strptime(vals['checkin'], DEFAULT_SERVER_DATETIME_FORMAT)
        date_end = datetime.strptime(vals['checkout'], DEFAULT_SERVER_DATETIME_FORMAT)
        date_diff = abs((date_start-date_end).days)

        hotel_vroom_obj = self.env['hotel.virtual.room']
        rooms_avail = []
        vrooms = self.env['hotel.virtual.room'].search([('room_ids.product_id', '=', vals['product_id'])])
        for vroom in vrooms:
            rdays = []
            for i in range(0, date_diff-1):
                ndate = date_start + timedelta(days=i)
                rdays.append({
                    'date': ndate.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': len(hotel_vroom_obj.check_availability_virtual_room(ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                                                                 ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                                                                 vroom.id))
                })
            ravail = {'id': vroom.wrid, 'days': rdays}
            rooms_avail.append(ravail)

        self.init_connection_()
        res, rcode = self.SERVER.update_sparse_avail(self.TOKEN,
                                                     self.LCODE,
                                                     rooms_avail)
        self.close_connection_()

        if res != 0:
            raise UserError("Can't update rooms availability in WuBook!")

        return True

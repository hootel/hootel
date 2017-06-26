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

    @api.model
    def initialize(self):
        self.push_activation()
        self.import_rooms()
#         self.fetch_new_bookings()
        return True

    # NETWORK
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
    def push_activation(self):
        errors = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url').replace("http://", "https://")

        self.init_connection_()

        rcode, results = self.SERVER.push_activation(self.TOKEN,
                                                     self.LCODE,
                                                     urljoin(base_url, "/wubook/push/reservations"),
                                                     1)
        if rcode != 0:
            errors.append("Can't activate push reservations: %s" % results)

        rcode, results = self.SERVER.push_update_activation(self.TOKEN,
                                                            self.LCODE,
                                                            urljoin(base_url, "/wubook/push/rooms"))
        if rcode != 0:
            errors.append("Can't activate push rooms: %s" % results)

        self.close_connection_()

        if any(errors):
            raise UserError('\n'.join(errors))

        return True

    # ROOMS
    @api.model
    def create_room(self, name, capacity, price, availability):
        self.init_connection_()
        shortcode = self.env['ir.sequence'].get('seq_vroom_id')
        rcode, results = self.SERVER.new_room(
            self.TOKEN,
            self.LCODE,
            0,
            name,
            capacity,
            price,
            availability,
            shortcode[:4],
            'nb'
#             rtype=('name' in vals and vals['name'] and 3) or 1
        )
        self.close_connection_()

        if rcode != 0:
            raise UserError("Can't create room in WuBook: %s" % results)

        return results

    @api.model
    def modify_room(self, rid, name, capacity, price, availability, scode):
        self.init_connection_()
        rcode, results = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            rid,
            name,
            capacity,
            price,
            availability,
            scode,
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )
        self.close_connection_()

        if rcode != 0:
            raise UserError("Can't modify room in WuBook: %s" % results)

        return True

    @api.model
    def delete_room(self, wrid):
        self.init_connection_()
        rcode, results = self.SERVER.del_room(
            self.TOKEN,
            self.LCODE,
            wrid
        )
        self.close_connection_()

        if rcode != 0:
            raise UserError("Can't delete room in WuBook: %s" % results)

        return True

    @api.model
    def import_rooms(self):
        self.init_connection_()
        rcode, results = self.SERVER.fetch_rooms(
            self.TOKEN,
            self.LCODE,
            0
        )
        self.close_connection_()

        vroom_obj = self.env['hotel.virtual.room']
        if rcode == 0:
            for room in results:
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
            raise UserError("Can't import rooms from WuBook: %s" % results)

        return True

    @api.model
    def update_availability(self, rooms_avail):
        self.init_connection_()
        rcode, results = self.SERVER.update_sparse_avail(self.TOKEN,
                                                         self.LCODE,
                                                         rooms_avail)
        self.close_connection_()

        if rcode != 0:
            raise UserError("Can't update rooms availability in WuBook: %s" % results)

        return True

    @api.model
    def corporate_fetch(self):
        self.init_connection_()
        rcode, results = self.SERVER.corporate_fetchable_properties(self.TOKEN)
        self.close_connection_()

        _logger.info("CORPORATE FETCH");
        _logger.info(results)

        if rcode != 0:
            raise UserError("Can't call 'corporate_fetch' from WuBook: %s" % results)

        return True

    # RESERVATIONS
    @api.model
    def fetch_new_bookings(self):
        self.init_connection_()
        rcode, results = self.SERVER.fetch_new_bookings(self.TOKEN,
                                                        self.LCODE,
                                                        1,
                                                        0)
        if rcode == 0:
            processed_rids = self.generate_reservations(results)
            if any(processed_rids):
                rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                           self.LCODE,
                                                           processed_rids)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't process reservations from wubook: %s" % results)

        return True

    @api.model
    def fetch_booking(self, lcode, wrid):
        self.init_connection_()
        rcode, results = self.SERVER.fetch_booking(self.TOKEN,
                                                   lcode,
                                                   wrid)
        if rcode == 0:
            processed_rids = self.generate_reservations(results)
            if any(processed_rids):
                rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                           lcode,
                                                           processed_rids)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't process reservations from wubook: %s" % results)

        return True

    @api.model
    def create_plan(self, name, daily=1):
        self.init_connection_()
        rcode, results = self.SERVER.add_pricing_plan(self.TOKEN,
                                                      self.LCODE,
                                                      name,
                                                      daily)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't add pricing plan to wubook: %s" % results)

        return results

    @api.model
    def delete_plan(self, pid):
        self.init_connection_()
        rcode, results = self.SERVER.del_plan(self.TOKEN,
                                              self.LCODE,
                                              pid)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't delete pricing plan from wubook: %s" % results)

        return True

    @api.model
    def update_plan_name(self, pid, name):
        self.init_connection_()
        rcode, results = self.SERVER.update_plan_name(self.TOKEN,
                                                      self.LCODE,
                                                      pid,
                                                      name)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't update pricing plan name in wubook: %s" % results)

        return True

    @api.model
    def update_plan_periods(self, pid, periods):
        _logger.info(periods)
        self.init_connection_()
        rcode, results = self.SERVER.update_plan_periods(self.TOKEN,
                                                         self.LCODE,
                                                         pid,
                                                         periods)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't update pricing plan name in wubook: %s" % results)

        return True

    @api.model
    def get_pricing_plans(self):
        self.init_connection_()
        rcode, results = self.SERVER.get_pricing_plans(self.TOKEN,
                                                       self.LCODE)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't get pricing plans from wubook: %s" % results)
        else:
            self.generate_pricelists(results)

        return True

    @api.model
    def fetch_plan_prices(self, pid, dfrom, dto, rooms=[]):
        _logger.info(dfrom)
        _logger.info(dto)
        _logger.info(pid)
        self.init_connection_()
        rcode, results = self.SERVER.fetch_plan_prices(self.TOKEN,
                                                       self.LCODE,
                                                       pid,
                                                       dfrom,
                                                       dto,
                                                       rooms)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't fetch plan prices from wubook: %s" % results)
        else:
            self.generate_pricelist_items(pid, dfrom, dto, results)

        return True

    @api.model
    def create_reservation(self, reserv):
        self.init_connection_()
        vroom = self.env['hotel.virtual.room'].search([('product_id', '=', reserv.product_id.id)], limit=1)
        customer = {
            'lname': _partner_split_name(reserv.partner_id.name)[1],
            'fname': _partner_split_name(reserv.partner_id.name)[0],
            'email': reserv.partner_id.email,
            'city': reserv.partner_id.city,
            'phone': reserv.partner_id.phone,
            'street': reserv.partner_id.street,
            'country': reserv.partner_id.country_id.code,
            'arrival_hour': datetime.strptime(reserv.checkin, "%H:%M:%S"),
            'notes': ''     # TODO: Falta poner el cajetin de observaciones en folio o reserva..
        }
        rcode, results = self.SERVER.new_reservation(self.TOKEN,
                                                     self.LCODE,
                                                     reserv.checkin,
                                                     reserv.checkout,
                                                     {vroom.wrid: [reserv.adults+reserv.children, 'nb']},
                                                     customer,
                                                     reserv.adults+reserv.children)
        self.close_connection_()

        if rcode == 0:
            reserv.write({'wrid': results})
        else:
            ValidationError("Can't create reservations in wubook: %s" % results)

        return True

    @api.model
    def cancel_reservation(self, wrid, reason=""):
        self.init_connection_()
        rcode, results = self.SERVER.cancel_reservation(self.TOKEN,
                                                        self.LCODE,
                                                        wrid,
                                                        reason)
        self.close_connection_()

        if rcode != 0:
            raise ValidationError("Can't cancel reservation in WuBook: %s" % results)

        return True

    @api.model
    def generate_pricelist_items(self, pid, dfrom, dto, plan_prices):
        pricelist = self.env['product.pricelist'].search([('wpid', '=', pid)], limit=1)
        if pricelist:
            dfrom_dt = datetime.strptime(dfrom, DEFAULT_WUBOOK_DATE_FORMAT)
            dto_dt = datetime.strptime(dto, DEFAULT_WUBOOK_DATE_FORMAT)
            days_diff = abs((dto_dt - dfrom_dt).days)
            for i in range(0, days_diff):
                ndate_dt = dfrom_dt + timedelta(days=i)
                for rid in plan_prices.keys():
                    vroom = self.env['hotel.virtual.room'].search([('wrid', '=', rid)], limit=1)
                    if vroom:
                        pricelist_item = self.env['product.pricelist.item'].search([
                            ('pricelist_id', '=', pricelist.id),
                            ('date_start', '=', ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                            ('date_end', '=', ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                            ('compute_price', '=', 'fixed'),
                            ('applied_on', '=', '1_product'),
                            ('product_tmpl_id', '=', vroom.product_id.product_tmpl_id.id)
                        ], limit=1)
                        vals = {
                            'fixed_price': plan_prices[rid][i],
                        }
                        if pricelist_item:
                            pricelist_item.with_context({'wubook_action': False}).write(vals)
                        else:
                            vals.update({
                                'pricelist_id': pricelist.id,
                                'date_start': ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                'date_end': ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                'compute_price': 'fixed',
                                'applied_on': '1_product',
                                'product_tmpl_id': vroom.product_id.product_tmpl_id.id
                            })
                            self.env['product.pricelist.item'].with_context({'wubook_action': False}).create(vals)

    @api.model
    def generate_pricelists(self, price_plans):
        product_listprice_obj = self.env['product.pricelist']
        for plan in price_plans:
            if 'vpid' in plan:
                continue    # Ignore Virtual Plans

            vals = {
                'name': plan['name'],
                'wdaily': plan['daily'] == 1,
            }
            plan_id = product_listprice_obj.search([('wpid', '=', str(plan['id']))], limit=1)
            if not plan_id:
                vals.update({'wpid': str(plan['id'])})
                product_listprice_obj.with_context({'wubook_action': False}).create(vals)
            else:
                plan_id.with_context({'wubook_action': False}).write(vals)

    @api.model
    def generate_reservations(self, bookings):
        res_partner_obj = self.env['res.partner']
        hotel_reserv_obj = self.env['hotel.reservation']
        hotel_folio_obj = self.env['hotel.folio']
        hotel_vroom_obj = self.env['hotel.virtual.room']
        processed_rids = []
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
                        'to_read': True,
                    })

                    if book['status'] in [WUBOOK_STATUS_CANCELLED,
                                          WUBOOK_STATUS_REFUSED]:
                        reserv.action_cancel()
                processed_rids.append(book['reservation_code'])
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
                    'phone': book['customer_phone'],
                    'zip': book['customer_zip'],
                    'street': book['customer_address'],
                    'email': book['customer_mail'],
                    #'lang': lang and lang.id,
                }
                partner_id = res_partner_obj.create(vals)

            # Obtener habitacion libre
            arr_hour = book['arrival_hour'] == "--" and '00:00' or book['arrival_hour']
            checkin = "%s %s" % (book['date_arrival'], arr_hour)
            checkin_dt = datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT)
            checkin = checkin_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            checkout = "%s 21:59" % book['date_departure']  # FIXME: Usar UTC
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

                    rstate = 'draft'
                    if book['status'] == WUBOOK_STATUS_CANCELLED \
                            or book['status'] == WUBOOK_STATUS_REFUSED:
                        rstate = 'cancelled'
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
                        'to_read': True,
                        'state': rstate,
                    }
                    reservations.append((0, False, vals))
                else:
                    raise ValidationError("Can't found a free room for reservation from wubook!!!")
            # Create Folio
            vals = {
                'room_lines': reservations,
                'wcustomer_notes': book['customer_notes'],
            }
            session_seed = book.get('sessionSeed', '')
            session_seed = session_seed != '' and session_seed
            hotel_folio_id = session_seed and hotel_folio_obj.search([('wseed', '=', session_seed)], limit=1)
            if hotel_folio_id:
                hotel_folio_id.with_context({'wubook_action': False}).write(vals)
            else:
                vals.update({
                    'partner_id': partner_id.id,
                    'wseed': book['sessionSeed']
                })
                hotel_folio_id = hotel_folio_obj.with_context({'wubook_action': False}).create(vals)
            processed_rids.append(book['reservation_code'])
        return processed_rids

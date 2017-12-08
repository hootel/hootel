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
import xmlrpclib
import pytz
from datetime import datetime, timedelta
from urlparse import urljoin
from openerp import models, api, fields
from openerp.exceptions import UserError, ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.payment.models.payment_acquirer import _partner_split_name
import logging
_logger = logging.getLogger(__name__)

# GLOBAL VARS
DEFAULT_WUBOOK_DATE_FORMAT = "%d/%m/%Y"
DEFAULT_WUBOOK_TIME_FORMAT = "%H:%M"
DEFAULT_WUBOOK_DATETIME_FORMAT = "%s %s" % (DEFAULT_WUBOOK_DATE_FORMAT,
                                            DEFAULT_WUBOOK_TIME_FORMAT)
WUBOOK_STATUS_CONFIRMED = 1
WUBOOK_STATUS_WAITING = 2
WUBOOK_STATUS_REFUSED = 3
WUBOOK_STATUS_ACCEPTED = 4
WUBOOK_STATUS_CANCELLED = 5
WUBOOK_STATUS_CANCELLED_PENALTY = 6

WUBOOK_STATUS_GOOD = [WUBOOK_STATUS_CONFIRMED, WUBOOK_STATUS_WAITING, WUBOOK_STATUS_ACCEPTED]
WUBOOK_STATUS_BAD = [WUBOOK_STATUS_REFUSED, WUBOOK_STATUS_CANCELLED, WUBOOK_STATUS_CANCELLED_PENALTY]


# WUBOOK
class WuBook(models.TransientModel):
    _name = 'wubook'

    # === INITALIZATION
    def __init__(self, pool, cr):
        super(WuBook, self).__init__(pool, cr)
        self.SERVER = False
        self.LCODE = False
        self.TOKEN = False

    @api.model
    def initialize(self, activate):
        self_context = self.with_context({'init_connection': False})
        if not self_context.init_connection():
            return False
        if activate:
            if not self_context.push_activation():
                return False

        res = (self_context.import_rooms()[0]
            and self_context.import_channels_info()[0]
            and self_context.import_pricing_plans()[0]
            and self_context.import_restriction_plans()[0])

        self.close_connection()
        return res

    @api.model
    def push_activation(self):
        errors = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url').replace("http://", "https://")

        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode_a, results_a = self.SERVER.push_activation(self.TOKEN,
                                                         self.LCODE,
                                                         urljoin(base_url, "/wubook/push/reservations"),
                                                         1)
        rcode_ua, results_ua = self.SERVER.push_update_activation(self.TOKEN,
                                                                  self.LCODE,
                                                                  urljoin(base_url, "/wubook/push/rooms"))
        if init_connection:
            self.close_connection()

        if rcode_a != 0:
            self.create_wubook_issue('wubook',
                                     "Can't activate push reservations",
                                     results_a)
        if rcode_ua != 0:
            self.create_wubook_issue('wubook', "Can't activate push rooms",
                                     results_ua)

        return rcode_a == 0 and rcode_ua == 0

    def is_valid_account(self):
        user = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_user')
        passwd = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_passwd')
        lcode = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_lcode')
        pkey = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_pkey')
        server_addr = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_server')
        return (user and passwd and pkey and server_addr and lcode)

    # === NETWORK
    def init_connection(self):
        user = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_user')
        passwd = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_passwd')
        self.LCODE = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_lcode')
        pkey = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_pkey')
        server_addr = self.env['ir.values'].sudo().get_default('wubook.config.settings', 'wubook_server')

        if not user or not passwd or not pkey or not server_addr or not self.LCODE:
            self.create_wubook_issue('wubook', "Can't connect with WuBook! Perhaps account not configured...", "")
            return False

        try:
            self.SERVER = xmlrpclib.Server(server_addr)
            res, tok = self.SERVER.acquire_token(user, passwd, pkey)
            self.TOKEN = tok
            if res != 0:
                self.create_wubook_issue('wubook', "Can't connect with WuBook! Perhaps the account haven't a good configuration...", tok)
        except:
            self.create_wubook_issue('wubook', "Can't connect with WuBook! Please, check internet connection.", "")
            res = -1

        return res == 0

    def close_connection(self):
        self.SERVER.release_token(self.TOKEN)
        self.TOKEN = False
        self.SERVER = False

    # === HELPER FUNCTIONS
    @api.model
    def create_wubook_issue(self, section, message, wmessage, wid=False, dfrom=False, dto=False):
        self.env['wubook.issue'].create({
            'section': section,
            'message': message,
            'wid': wid,
            'wmessage': wmessage,
            'date_start': dfrom and datetime.strptime(dfrom, DEFAULT_WUBOOK_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'date_end': dto and datetime.strptime(dto, DEFAULT_WUBOOK_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT),
        })

    # === ROOMS
    @api.model
    def create_room(self, shortcode, name, capacity, price, availability):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.new_room(
            self.TOKEN,
            self.LCODE,
            0,
            name,
            capacity,
            price,
            availability,
            shortcode[:4],
            'nb'    # TODO: Complete this part
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room', "Can't create room in WuBook", results)
            return False

        return results

    @api.model
    def modify_room(self, wrid, name, capacity, price, availability, scode):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            wrid,
            name,
            capacity,
            price,
            availability,
            scode,
            'nb'
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room', "Can't modify room in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def delete_room(self, wrid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.del_room(
            self.TOKEN,
            self.LCODE,
            wrid
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room', "Can't delete room in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def import_rooms(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_rooms(
            self.TOKEN,
            self.LCODE,
            0
        )
        if init_connection:
            self.close_connection()

        vroom_obj = self.env['hotel.virtual.room']
        count = 0
        if rcode == 0:
            count = len(results)
            for room in results:
                vroom = vroom_obj.search([('wrid', '=', room['id'])], limit=1)
                vals = {
                    'name': room['name'],
                    'wrid': room['id'],
                    'wscode': room['shortname'],
                    'list_price': room['price'],
                    'wcapacity': room['occupancy'],
                    # 'max_real_rooms': room['availability'],
                }
                if vroom:
                    vroom.with_context({'wubook_action': False}).write(vals)
                else:
                    vroom_obj.with_context({'wubook_action': False}).create(vals)
        else:
            self.create_wubook_issue('room', "Can't import rooms from WuBook",
                                     results)

        return (rcode == 0, count)

    @api.model
    def fetch_rooms_values(self, dfrom, dto, rooms=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.fetch_rooms_values(self.TOKEN,
                                                        self.LCODE,
                                                        dfrom,
                                                        dto,
                                                        rooms)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room',
                                     "Can't fetch rooms values from WuBook",
                                     results, dfrom=dfrom, dto=dto)
        else:
            self.generate_room_values(dfrom, dto, results)

        return rcode == 0

    @api.model
    def update_availability(self, rooms_avail):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_sparse_avail(self.TOKEN,
                                                         self.LCODE,
                                                         rooms_avail)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room',
                                     "Can't update rooms availability in WuBook",
                                     results)

        return rcode == 0

    @api.model
    def corporate_fetch(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.corporate_fetchable_properties(self.TOKEN)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('wubook',
                                     "Can't call 'corporate_fetch' from WuBook",
                                     results)

        return rcode == 0

    # === RESERVATIONS
    @api.model
    def create_reservation(self, reserv):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
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
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't create reservations in wubook",
                                     results,
                                     dfrom=reserv.checkin, dto=reserv.checkout)
        else:
            reserv.write({'wrid': results})

        return rcode == 0

    @api.model
    def cancel_reservation(self, wrid, reason=""):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.cancel_reservation(self.TOKEN,
                                                        self.LCODE,
                                                        wrid,
                                                        reason)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't cancel reservation in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def fetch_new_bookings(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_new_bookings(self.TOKEN,
                                                        self.LCODE,
                                                        1,
                                                        0)
        errors = False
        processed_rids = []
        if rcode == 0:
            processed_rids, errors = self.generate_reservations(results)
            if any(processed_rids):
                rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                           self.LCODE,
                                                           processed_rids)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't process reservations from wubook",
                                     results)

        return ((rcode == 0 and not errors), len(processed_rids))

    @api.model
    def fetch_booking(self, lcode, wrid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_booking(self.TOKEN,
                                                   lcode,
                                                   wrid)
        errors = False
        processed_rids = []
        if rcode == 0:
            processed_rids, errors = self.generate_reservations(results)
            if any(processed_rids):
                _logger.info("[WuBook] PROCESSED Reservations:")
                _logger.info(processed_rids)
                rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                           lcode,
                                                           processed_rids)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't process reservations from wubook",
                                     results, wid=wrid)

        return ((rcode == 0 and not errors), len(processed_rids))

    @api.model
    def mark_bookings(self, wrids):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                   self.LCODE,
                                                   wrids)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't mark as readed a reservation in wubook",
                                     results, wid=wrid)

        return rcode == 0

    # === PRICE PLANS
    @api.model
    def create_plan(self, name, daily=1):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.add_pricing_plan(self.TOKEN,
                                                      self.LCODE,
                                                      name,
                                                      daily)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan', "Can't add pricing plan to wubook",
                                     results)
            return False

        return results

    @api.model
    def delete_plan(self, pid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.del_plan(self.TOKEN,
                                              self.LCODE,
                                              pid)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan',
                                     "Can't delete pricing plan from wubook",
                                     results,
                                     wid=pid)

        return rcode == 0

    @api.model
    def update_plan_name(self, pid, name):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_name(self.TOKEN,
                                                      self.LCODE,
                                                      pid,
                                                      name)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan',
                                     "Can't update pricing plan name in wubook",
                                     results, wid=pid)

        return rcode == 0

    @api.model
    def update_plan_prices(self, pid, dfrom, prices):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_prices(self.TOKEN,
                                                        self.LCODE,
                                                        pid,
                                                        dfrom,
                                                        prices)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan', "Can't update pricing plan in wubook",
                                     results, wid=pid, dfrom=dfrom)

        return rcode == 0

    @api.model
    def update_plan_periods(self, pid, periods):
        _logger.info("[WuBook] Updating Plan Periods...")
        _logger.info(periods)
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_periods(self.TOKEN,
                                                         self.LCODE,
                                                         pid,
                                                         periods)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan',
                                     "Can't update pricing plan period in wubook",
                                     results, wid=pid)

        return rcode == 0

    @api.model
    def import_pricing_plans(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.get_pricing_plans(self.TOKEN,
                                                       self.LCODE)
        if init_connection:
            self.close_connection()

        count = 0
        if rcode != 0:
            self.create_wubook_issue('plan', "Can't get pricing plans from wubook",
                                     results)
        else:
            count = self.generate_pricelists(results)

        return (rcode == 0, count)

    @api.model
    def fetch_plan_prices(self, pid, dfrom, dto, rooms=[]):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.fetch_plan_prices(self.TOKEN,
                                                       self.LCODE,
                                                       pid,
                                                       dfrom,
                                                       dto,
                                                       rooms)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan', "Can't fetch plan prices from wubook",
                                     results, wid=pid, dfrom=dfrom, dto=dto)
        else:
            self.generate_pricelist_items(pid, dfrom, dto, results)

        return rcode == 0

    @api.model
    def fetch_all_plan_prices(self, dfrom, dto, rooms=[]):
        no_errors = True
        plan_wpids = self.env['product.pricelist'].search([('wpid', '!=', False), ('wpid', '!=', '')]).mapped('wpid')
        if any(plan_wpids):
            init_connection = self._context.get('init_connection', True)
            if init_connection:
                if not self.init_connection():
                    return False
            for wpid in plan_wpids:
                rcode, results = self.SERVER.fetch_plan_prices(self.TOKEN,
                                                               self.LCODE,
                                                               wpid,
                                                               dfrom,
                                                               dto,
                                                               rooms)
                if rcode != 0:
                    self.create_wubook_issue('plan',
                                             "Can't fetch all plan prices from wubook!",
                                             results, wid=wpid, dfrom=dfrom, dto=dto)
                    no_errors = False
                else:
                    self.generate_pricelist_items(wpid, dfrom, dto, results)
            if init_connection:
                self.close_connection()

        return no_errors

    # === RESTRICTION PLANS
    @api.model
    def import_restriction_plans(self, init_connection=True):
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.rplan_rplans(self.TOKEN,
                                                  self.LCODE)
        if init_connection:
            self.close_connection()

        count = 0
        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't fetch restriction plans from wubook",
                                     results)
        else:
            count = self.generate_restrictions(results)

        return (rcode == 0, count)

    @api.model
    def fetch_rplan_restrictions(self, dfrom, dto, rpid=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_get_rplan_values(self.TOKEN,
                                                            self.LCODE,
                                                            dfrom,
                                                            dto,
                                                            rpid)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't fetch plan restrictions from wubook",
                                     results, wid=rpid, dfrom=dfrom, dto=dto)
        elif any(results):
            self.generate_restriction_items(dfrom, dto, results)

        return rcode == 0

    @api.model
    def update_rplan_values(self, rpid, dfrom, values):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_update_rplan_values(self.TOKEN,
                                                               self.LCODE,
                                                               rpid,
                                                               dfrom,
                                                               values)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't update plan restrictions on wubook",
                                     results, wid=rpid, dfrom=dfrom)

        return rcode == 0

    @api.model
    def create_rplan(self, name, compact=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_add_rplan(self.TOKEN,
                                                     self.LCODE,
                                                     name,
                                                     compact and 1 or 0)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't create plan restriction in wubook",
                                     results)
            return False

        return results

    @api.model
    def rename_rplan(self, rpid, name):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_rename_rplan(self.TOKEN,
                                                        self.LCODE,
                                                        rpid,
                                                        name)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't rename plan restriction in wubook",
                                     results, wid=rpid)

        return rcode == 0

    @api.model
    def delete_rplan(self, rpid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_del_rplan(self.TOKEN,
                                                     self.LCODE,
                                                     rpid)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't delete plan restriction on wubook",
                                     results, wid=rpid)

        return rcode == 0

    # === WUBOOK INFO
    @api.model
    def import_channels_info(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        results = self.SERVER.get_channels_info(self.TOKEN)
        if init_connection:
            self.close_connection()

        count = self.generate_wubook_channel_info(results)

        return (True, count)

    # === WUBOOK -> ODOO
    @api.model
    def generate_room_values(self, dfrom, dto, values):
        virtual_room_avail_obj = self.env['hotel.virtual.room.availabity']
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        for rid in values.keys():
            vroom = hotel_virtual_room_obj.search([('wrid', '=', rid)], limit=1)
            if vroom:
                date_dt = datetime.strptime(dfrom, DEFAULT_WUBOOK_DATE_FORMAT)
                for day_vals in values[rid]:
                    date_str = date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    vroom_avail = virtual_room_avail_obj.search([('virtual_room_id', '=', vroom.id),
                                                                 ('date', '=', date_str)], limit=1)
                    vals = {
                        'no_ota': day_vals.get('no_ota'),
                        'booked': day_vals.get('booked'),
                        'avail': 0 if not day_vals.get('avail') else day_vals['avail'],
                        'wpushed': True,
                    }
                    if vroom_avail:
                        vroom_avail.with_context({'wubook_action': False}).write(vals)
                    else:
                        vals.update({
                            'virtual_room_id': vroom.id,
                            'date': date_str,
                        })
                        virtual_room_avail_obj.with_context({'wubook_action': False}).create(vals)
                    date_dt = date_dt + timedelta(days=1)

        return True

    @api.model
    def generate_restrictions(self, restriction_plans):
        reservation_restriction_obj = self.env['hotel.virtual.room.restriction']
        count = 0
        for plan in restriction_plans:
            vals = {
                'name': plan['name'],
            }
            plan_id = reservation_restriction_obj.search([('wpid', '=', str(plan['id']))], limit=1)
            if not plan_id:
                vals.update({
                    'wpid': str(plan['id']),
                })
                reservation_restriction_obj.with_context({
                    'wubook_action': False,
                    'rules': plan.get('rules'),
                }).create(vals)
            else:
                plan_id.with_context({'wubook_action': False}).write(vals)
            count = count + 1
        return count

    @api.model
    def generate_restriction_items(self, dfrom, dto, plan_restrictions):
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        reserv_restriction_obj = self.env['hotel.virtual.room.restriction']
        reserv_restriction_item_obj = self.env['hotel.virtual.room.restriction.item']
        for rpid in plan_restrictions.keys():
            restriction_id = reserv_restriction_obj.search([('wpid', '=', rpid)], limit=1)
            if restriction_id:
                for rid in plan_restrictions[rpid].keys():
                    vroom = hotel_virtual_room_obj.search([('wrid', '=', rid)], limit=1)
                    if vroom:
                        for item in plan_restrictions[rpid][rid]:
                            date_dt = datetime.strptime(item['date'], DEFAULT_WUBOOK_DATE_FORMAT)
                            restriction_item = reserv_restriction_item_obj.search([
                                ('restriction_id', '=', restriction_id.id),
                                ('date_start', '=', date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('date_end', '=', date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('applied_on', '=', '0_virtual_room'),
                                ('virtual_room_id', '=', vroom.id)
                            ], limit=1)
                            vals = {
                                'closed_arrival': item['closed_arrival'],
                                'closed': item['closed'],
                                'min_stay': item['min_stay'],
                                'closed_departure': item['closed_departure'],
                                'max_stay': item['max_stay'],
                                'min_stay_arrival': item['min_stay_arrival'],
                                'wpushed': True,
                            }
                            if restriction_item:
                                restriction_item.with_context({'wubook_action': False}).write(vals)
                            else:
                                vals.update({
                                    'restriction_id': restriction_id.id,
                                    'date_start': date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    'date_end': date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                    'applied_on': '0_virtual_room',
                                    'virtual_room_id': vroom.id
                                })
                                self.env['hotel.virtual.room.restriction.item'].with_context({'wubook_action': False}).create(vals)

        return True

    @api.model
    def generate_pricelist_items(self, pid, dfrom, dto, plan_prices):
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        pricelist = self.env['product.pricelist'].search([('wpid', '=', pid)], limit=1)
        if pricelist:
            dfrom_dt = datetime.strptime(dfrom, DEFAULT_WUBOOK_DATE_FORMAT)
            dto_dt = datetime.strptime(dto, DEFAULT_WUBOOK_DATE_FORMAT)
            days_diff = abs((dto_dt - dfrom_dt).days) + 1
            for i in range(0, days_diff):
                ndate_dt = dfrom_dt + timedelta(days=i)
                for rid in plan_prices.keys():
                    vroom = hotel_virtual_room_obj.search([('wrid', '=', rid)], limit=1)
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
                            'wpushed': True,
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
        return True

    @api.model
    def generate_pricelists(self, price_plans):
        product_listprice_obj = self.env['product.pricelist']
        count = 0
        for plan in price_plans:
            if 'vpid' in plan:
                continue    # Ignore Virtual Plans

            vals = {
                'name': plan['name'],
                'wdaily': plan['daily'] == 1,
            }
            plan_id = product_listprice_obj.search([('wpid', '=', str(plan['id']))], limit=1)
            if not plan_id:
                vals.update({
                    'wpid': str(plan['id']),
                })
                product_listprice_obj.with_context({'wubook_action': False}).create(vals)
            else:
                plan_id.with_context({'wubook_action': False}).write(vals)
            count = count + 1
        return count

    # FIXME: Super big method!!! O_o
    @api.model
    def generate_reservations(self, bookings):
        default_arrival_hour = self.env['ir.values'].get_default('hotel.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.values'].get_default('hotel.config.settings', 'default_departure_hour')

        # Use specific method because others include connection step
        def fetch_values(dfrom, dto):
            rcode, results = self.SERVER.fetch_rooms_values(self.TOKEN,
                                                            self.LCODE,
                                                            dfrom,
                                                            dto,
                                                            False)
            if rcode != 0:
                self.create_wubook_issue('room',
                                         "Can't fetch rooms values from WuBook",
                                         results, dfrom=dfrom, dto=dto)
            else:
                self.generate_room_values(dfrom, dto, results)

        user_id = self.env['res.users'].browse(self.env.uid)
        local = pytz.timezone(user_id and user_id.tz or 'UTC')
        res_partner_obj = self.env['res.partner']
        hotel_reserv_obj = self.env['hotel.reservation']
        hotel_folio_obj = self.env['hotel.folio']
        hotel_vroom_obj = self.env['hotel.virtual.room']
        vroom_avail_obj = self.env['hotel.virtual.room.availabity']
        processed_rids = []
        failed_reservations = []
        _logger.info(bookings)
        for book in bookings:
            is_cancellation = book['status'] in WUBOOK_STATUS_BAD

            # Can't process failed reservations
            if book['channel_reservation_code'] in failed_reservations:
                self.create_wubook_issue('reservation',
                                         "Can't process a reservation that previusly failed!",
                                         '', wid=book['reservation_code'])
                continue

            arr_hour = book['arrival_hour'] == "--" and default_arrival_hour or book['arrival_hour']
            checkin = "%s %s" % (book['date_arrival'], arr_hour)
            checkin_dt = local.localize(datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT))
            checkin_utc_dt = checkin_dt.astimezone(pytz.utc)
            checkin = checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            checkout = "%s %s" % (book['date_departure'], default_departure_hour)
            checkout_dt = local.localize(datetime.strptime(checkout, DEFAULT_WUBOOK_DATETIME_FORMAT))
            checkout_utc_dt = checkout_dt.astimezone(pytz.utc)
            checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            today = datetime.strftime(fields.datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)

            # Search Folio. If exists.
            folio_id = False
            if book['channel_reservation_code'] and book['channel_reservation_code'] != '':
                reserv_folio = hotel_reserv_obj.search([('wchannel_reservation_code', '=', str(book['channel_reservation_code']))], limit=1)
                if reserv_folio:
                    folio_id = reserv_folio.folio_id
            else:
                reserv_folio = hotel_reserv_obj.search([('wrid', '=', str(book['reservation_code']))], limit=1)
                if reserv_folio:
                    folio_id = reserv_folio.folio_id

            reservs = folio_id and folio_id.room_lines or hotel_reserv_obj.search([('wrid', '=', str(book['reservation_code']))])
            reservs_processed = False
            if any(reservs):
                folio_id = reservs[0].folio_id
                for reserv in reservs:
                    if reserv.wrid == str(book['reservation_code']):
                        reserv.with_context({'wubook_action': False}).write({
                            'wstatus': str(book['status']),
                            'wstatus_reason': book.get('status_reason', ''),
                            'to_read': True,
                        })
                        reservs_processed = True
                        if is_cancellation:
                            reserv.with_context({'wubook_action': False}).action_cancel()

            # Do Nothing if already processed 'wrid'
            if reservs_processed:
                processed_rids.append(book['reservation_code'])
                # Update Odoo availability (don't wait for wubook)
                fetch_values(checkin_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                             checkout_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
                continue

            # Search Customer
            country_id = self.env['res.country'].search([('code', '=', book['customer_country'])], limit=1)
            customer_mail = book.get('customer_mail', False)
            partner_id = False
            if customer_mail:
                partner_id = res_partner_obj.search([('email', '=', customer_mail)], limit=1)
            if not partner_id:
                # lang = self.env['res.lang'].search([('code', '=', book['customer_language_iso'])], limit=1)
                vals = {
                    'name': "%s %s" % (book['customer_name'], book['customer_surname']),
                    'country_id': country_id and country_id.id,
                    'city': book['customer_city'],
                    'phone': book['customer_phone'],
                    'zip': book['customer_zip'],
                    'street': book['customer_address'],
                    'email': book['customer_mail'],
                    'unconfirmed': True,
                    # 'lang': lang and lang.id,
                }
                partner_id = res_partner_obj.create(vals)
            # Search Wubook Channel Info
            wchannel_info = self.env['wubook.channel.info'].search(
                [('wid', '=', str(book['id_channel']))], limit=1)

            # Obtener habitacion libre
            vrooms_ids = book['rooms'].split(',')
            vrooms = hotel_vroom_obj.search([('wrid', 'in', vrooms_ids)])

            reservations = []
            used_rooms = []
            # Check reservation vrooms avail
            for vroom in vrooms:
                dates_checkin = [checkin_utc_dt, False]
                dates_checkout = [checkout_utc_dt, False]
                split_booking = False
                split_map_index = {}
                parent_reservation = -1
                while dates_checkin[0]:
                    checkin_str = dates_checkin[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    checkout_str = dates_checkout[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)

                    free_rooms = hotel_vroom_obj.check_availability_virtual_room(checkin_str,
                                                                                 checkout_str,
                                                                                 virtual_room_id=vroom.id,
                                                                                 notthis=used_rooms)
                    if any(free_rooms):
                        num_free_rooms = len(free_rooms)
                        # Total Price Room
                        reservation_lines = []
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
                        customer_room_index = 0
                        for broom in book['rooms_occupancies']:
                            if str(broom['id']) == vroom.wrid:
                                if num_free_rooms > customer_room_index:
                                    occupancy = broom['occupancy']
                                    vals = {
                                        'checkin': checkin_str,
                                        'checkout': checkout_str,
                                        'adults': occupancy,
                                        'children': 0,
                                        'product_id': free_rooms[customer_room_index].product_id.id,
                                        'product_uom': free_rooms[customer_room_index].product_id.product_tmpl_id.uom_id.id,
                                        'product_uom_qty': 1,
                                        'reservation_lines': reservation_lines,
                                        'name': free_rooms[customer_room_index].name,
                                        'price_unit': tprice,
                                        'to_assign': not is_cancellation,
                                        'wrid': str(book['reservation_code']),
                                        'wchannel_id': wchannel_info and wchannel_info.id,
                                        'wchannel_reservation_code': str(book['channel_reservation_code']),
                                        'wstatus': str(book['status']),
                                        'to_read': True,
                                        'state': is_cancellation and 'cancelled' or 'draft',
                                        'virtual_room_id': vroom.id,
                                        'splitted': split_booking,
                                    }
                                    reservations.append((0, False, vals))
                                    if split_booking:
                                        if parent_reservation == -1:
                                            parent_reservation = len(reservations)-1
                                            split_map_index = { parent_reservation: [] }
                                        else:
                                            split_map_index[parent_reservation].append(len(reservations)-1)
                                    used_rooms.append(free_rooms[customer_room_index].id)
                                    customer_room_index += 1
                                else:
                                    if book['channel_reservation_code'] and book['channel_reservation_code'] != '':
                                        failed_reservations.append(book['channel_reservation_code'])
                                    else:
                                        failed_reservations.append('undefined')
                                    self.create_wubook_issue('reservation',
                                                             "Can't found a free room for reservation from wubook (#B)",
                                                             '', wid=book['reservation_code'])

                        dates_checkin = [dates_checkin[1], False]
                        dates_checkout = [dates_checkout[1], False]
                    else:
                        split_booking = True
                        date_diff = (dates_checkout[0] - dates_checkin[0]).days
                        if date_diff <= 0:
                            if book['channel_reservation_code'] and book['channel_reservation_code'] != '':
                                failed_reservations.append(book['channel_reservation_code'])
                            else:
                                failed_reservations.append('undefined')
                            self.create_wubook_issue('reservation',
                                                     "Can't found a free room for reservation from wubook",
                                                     '', wid=book['reservation_code'])
                            dates_checkin = [False, False]
                            dates_checkout = [False, False]
                        else:
                            dates_checkin = [dates_checkin[0], dates_checkin[0] + timedelta(days=date_diff - 1)]
                            dates_checkout = [dates_checkout[0] - timedelta(days=1), dates_checkout[0]]

            # Create Folio
            if not any(failed_reservations) and any(reservations):
                vals = {
                    'room_lines': reservations,
                    'wcustomer_notes': book['customer_notes'],
                }
                if folio_id:
                    folio_id.with_context({'wubook_action': False}).write(vals)
                else:
                    vals.update({
                        'partner_id': partner_id.id,
                        'wseed': book['sessionSeed']
                    })
                    folio_id = hotel_folio_obj.with_context({'wubook_action': False}).create(vals)
                processed_rids.append(book['reservation_code'])

            # Update Reservation Split Parent
            # FIXME: Ugly to read and execute
            master_ids = split_map_index.keys()
            if folio_id and any(master_ids):
                reservation_ids = hotel_reserv_obj.search([('folio_id', '=', folio_id.id)])
                master_reserv = False
                for mid in master_ids:
                    counter = 0
                    for reserv in reservation_ids:
                        child_ids = master_ids[mid]
                        for child in child_ids:
                            if child == counter:
                                reserv.parent_reservation = master_reserv.id
                            elif child == mid:
                                master_reserv = reservs
                                counter = counter + 1
                self.create_wubook_issue('reservation',
                     "Reservation Splitted",
                     '', wid=book['reservation_code'])

            # Update Odoo availability (don't wait for wubook)
            fetch_values(checkin_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                         checkout_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
        return (processed_rids, any(failed_reservations))

    @api.model
    def generate_wubook_channel_info(self, channels):
        channel_info_obj = self.env['wubook.channel.info']
        count = 0
        for cid in channels.keys():
            vals = {
                'name': channels[cid]['name'],
                'ical': channels[cid]['ical'] == 1,
            }
            channel_info = channel_info_obj.search([('wid', '=', cid)], limit=1)
            if channel_info:
                channel_info.write(vals)
            else:
                vals.update({
                    'wid': cid
                })
                channel_info_obj.create(vals)
            count = count + 1
        return count

    # === ODOO -> WUBOOK
    @api.model
    def push_changes(self):
        return self.push_availability() and self.push_priceplans() and self.push_restrictions()

    @api.model
    def push_availability(self):
        vroom_avail_ids = self.env['hotel.virtual.room.availabity'].search([
            ('wpushed', '=', False),
            ('date', '>=', datetime.strftime(fields.datetime.now(), DEFAULT_SERVER_DATE_FORMAT))
        ])

        vrooms = vroom_avail_ids.mapped('virtual_room_id')
        avails = []
        for vroom in vrooms:
            vroom_avails = vroom_avail_ids.filtered(lambda x: x.virtual_room_id.id == vroom.id)
            days = []
            for vroom_avail in vroom_avails:
                vroom_avail.with_context({'wubook_action': False}).write({'wpushed': True})
                date_dt = datetime.strptime(vroom_avail.date, DEFAULT_SERVER_DATE_FORMAT)
                days.append({
                    'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': vroom_avail.avail,
                    'no_ota': vroom_avail.no_ota and 1 or 0,
                    # 'booked': vroom_avail.booked and 1 or 0,
                })
            avails.append({'id': vroom.wrid, 'days': days})
        _logger.info(avails)
        if any(avails):
            self.update_availability(avails)
        return True

    @api.model
    def push_priceplans(self):
        unpushed = self.env['product.pricelist.item'].search([('wpushed', '=', False),
                                                              ('date_start', '>=', datetime.strftime(fields.datetime.now(), DEFAULT_SERVER_DATE_FORMAT))],
                                                             order="date_start ASC")
        if any(unpushed):
            date_start = datetime.strptime(unpushed[0].date_start, DEFAULT_SERVER_DATE_FORMAT)
            date_end = datetime.strptime(unpushed[-1].date_start, DEFAULT_SERVER_DATE_FORMAT)
            days_diff = abs((date_end-date_start).days) + 1

            prices = {}
            pricelist_ids = self.env['product.pricelist'].search([('wpid', '!=', False),
                                                                  ('active', '=', True)])
            for pr in pricelist_ids:
                prices.update({pr.wpid: {}})
                unpushed_pl = self.env['product.pricelist.item'].search(
                    [('wpushed', '=', False), ('pricelist_id', '=', pr.id)])
                product_tmpl_ids = unpushed_pl.mapped('product_tmpl_id')
                for pt_id in product_tmpl_ids:
                    vroom = self.env['hotel.virtual.room'].search([('product_id.product_tmpl_id', '=', pt_id.id)], limit=1)
                    if vroom:
                        prices[pr.wpid].update({vroom.wrid: []})
                        for i in range(0, days_diff):
                            prod = vroom.product_id.with_context({
                                    'quantity': 1,
                                    'pricelist': pr.id,
                                    'date': (date_start + timedelta(days=i)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                                })
                            prices[pr.wpid][vroom.wrid].append(prod.price)
            _logger.info(prices)
            plan_keys = prices.keys()
            for pk in plan_keys:
                if any(prices[pk]):
                    self.update_plan_prices(pk, date_start.strftime(DEFAULT_WUBOOK_DATE_FORMAT), prices[pk])

            for pli in unpushed:
                pli.with_context({'wubook_action': False}).write({'wpushed': True})
        return True

    @api.model
    def push_restrictions(self):
        unpushed = self.env['hotel.virtual.room.restriction.item'].search([('wpushed', '=', False),
                                                                    ('date_start', '>=', datetime.strftime(fields.datetime.now(), DEFAULT_SERVER_DATE_FORMAT))],
                                                                   order="date_start ASC")
        if any(unpushed):
            date_start = datetime.strptime(unpushed[0].date_start, DEFAULT_SERVER_DATE_FORMAT)
            date_end = datetime.strptime(unpushed[-1].date_start, DEFAULT_SERVER_DATE_FORMAT)
            days_diff = abs((date_end-date_start).days) + 1

            restrictions = {}
            restriction_plan_ids = self.env['hotel.virtual.room.restriction'].search([('wpid', '!=', False),
                                                                               ('active', '=', True)])
            for rp in restriction_plan_ids:
                restrictions.update({rp.wpid: {}})
                unpushed_rp = self.env['hotel.virtual.room.restriction.item'].search(
                    [('wpushed', '=', False), ('restriction_id', '=', rp.id)])
                virtual_room_ids = unpushed_rp.mapped('virtual_room_id')
                for vroom in virtual_room_ids:
                    restrictions[rp.wpid].update({vroom.wrid: []})
                    for i in range(0, days_diff):
                        restr = vroom.get_restrictions(date_start.strftime(DEFAULT_SERVER_DATE_FORMAT))
                        restrictions[rp.wpid][vroom.wrid].append({
                            'min_stay': restr and restr.min_stay or 0,
                            'min_stay_arrival': restr and restr.min_stay_arrival or 0,
                            'max_stay': restr and restr.max_stay or 0,
                            'closed': (restr and restr.closed) and 1 or 0,
                            'closed_arrival': (restr and restr.closed_arrival) and 1 or 0,
                            'closed_departure': (restr and restr.closed_departure) and 1 or 0,
                        })
            _logger.info(restrictions)
            plan_keys = restrictions.keys()
            for pk in plan_keys:
                if any(restrictions[pk]):
                    self.update_rplan_values(pk,
                                             date_start.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                                             restrictions[pk])
            for rpi in unpushed:
                rpi.with_context({'wubook_action': False}).write({'wpushed': True})
        return True

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import xmlrpclib
import openerp
from openerp.models import BaseModel
from openerp import models, api
import logging
_logger = logging.getLogger(__name__)


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

        return res

    def close_connection_(self):
        self.SERVER.release_token(self.TOKEN)
        self.TOKEN = False
        self.SERVER = False

    @api.multi
    def create_room(self, vroomid):
        isConnected = self.init_connection_()
        if not isConnected:
            return False

        vroom = self.env['hotel.virtual.room'].browse([vroomid])

        shortcode = self.env['ir.sequence'].get('seq_vroom_id')

        res, rid = self.SERVER.new_room(
            self.TOKEN,
            self.LCODE,
            0,
            vroom.name,
            2,
            vroom.list_price,
            vroom.max_real_rooms,
            shortcode[:4],
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )

        self.close_connection_()

        vroom.write({'wrid': rid})
        return True

    @api.multi
    def modify_room(self, vroomid):
        isConnected = self.init_connection_()
        if not isConnected:
            return False

        vroom = self.env['hotel.virtual.room'].browse([vroomid])

        res, rid = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            vroom.wrid,
            vroom.name,
            2,
            vroom.list_price,
            vroom.max_real_rooms,
            vroom.wscode,
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )

        self.close_connection_()
        return True

    @api.multi
    def push_prices(self):

        if True:
            return True

        isConnected = self.init_connection_()
        if not isConnected:
            return False

        vroom = self.env['hotel.virtual.room'].browse([])

        res, rid = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            vroom.wrid,
            vroom.name,
            2,
            vroom.list_price,
            vroom.max_real_rooms,
            vroom.wscode,
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )

        self.close_connection_()
        return True

    @api.multi
    def push_activation(self):
        isConnected = self.init_connection_()
        if not isConnected:
            return False

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        res = self.SERVER.push_activation(self.TOKEN,
                                          self.LCODE,
                                          urljoin(base_url, "/wubook/push"), 1)

        self.close_connection_()
        return True

    @api.multi
    def corporate_fetch(self):
        isConnected = self.init_connection_()
        if not isConnected:
            return False

        res = self.SERVER.corporate_fetchable_properties(self.TOKEN)

        self.close_connection_()
        return True

    @api.multi
    def fetch_new_bookings(self):
        isConnected = self.init_connection_()
        if not isConnected:
            return False

        res, bookings = self.SERVER.fetch_new_bookings(self.TOKEN,
                                                       self.LCODE,
                                                       1,
                                                       0)
        _logger.info("FETCH NEW BOOKINGS")
        _logger.info(res)
        _logger.info(bookings)

        self.close_connection_()
        return True

    @api.multi
    def initialize(self):
        _logger.info("INITIALIZE WUBOOK")
        noErrors = self.push_activation()
        if noErrors:
            noErrors = self.fetch_new_bookings()
        return noErrors

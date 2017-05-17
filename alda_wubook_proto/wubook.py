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

    @api.multi
    def create_room(self, vals):
        user_r = self.env['res.users'].browse(self.env.uid)

        user = user_r.partner_id.wubook_user
        passwd = user_r.partner_id.wubook_passwd
        lcode = user_r.partner_id.wubook_lcode
        pkey = user_r.partner_id.wubook_pkey
        wserver = user_r.partner_id.wubook_server

        _logger.info("PASA 11")
        _logger.info(user)
        _logger.info(passwd)
        _logger.info(lcode)
        _logger.info(pkey)
        _logger.info(wserver)

        wServer = xmlrpclib.Server(wserver)
        res, tok = wServer.acquire_token(user, passwd, pkey)

        _logger.info("PASA 22")

        _logger.info(res)
        _logger.info(tok)
        shortcode = "V%s" % vals['name']

        _logger.info(shortcode)

        res, rid = wServer.new_room(
            tok,
            lcode,
            0,
            vals['name'],
            2,
            900,
            1,
            shortcode[:4],
            'nb'
            #rtype=('name' in vals and vals['name'] and 3) or 1
        )

        wServer.release_token(tok)

        vals.update({'virtual_code': rid})

        _logger.info("PASA FIN")
        _logger.info(res)
        _logger.info(vals)

        return vals


# CREATE
create_original = BaseModel.create


@api.model
@api.returns('self', lambda value: value.id)
def create(self, vals):
    nvals = wubook_handle_create(self, vals)
    _logger.info("NVALS")
    _logger.info(nvals)
    record_id = create_original(self, nvals)
    return record_id


BaseModel.create = create


# WRITE
write_original = BaseModel.write


@api.multi
def write(self, vals):
    result = write_original(self, vals)
#     auto_refresh_kanban_list(self)
    return result


BaseModel.write = write


# UNLINK
unlink_original = BaseModel.unlink


@api.multi
def unlink(self):
    result = unlink_original(self)
#     auto_refresh_kanban_list(self)
    return result


BaseModel.unlink = unlink


def wubook_handle_create(model, vals):
    if model._name == 'hotel.virtual.room':
        return model.env['wubook'].create_room(vals)
    return vals

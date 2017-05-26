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
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.event import on_record_write, on_record_create
import logging
_logger = logging.getLogger(__name__)


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with.  """
    backend_record = session.env['magento.backend'].browse(backend_id)
    env = ConnectorEnvironment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env


# BINDINDS
class WuBookRoom(models.Model):
    _name = 'wubook.hotel.virtual.room'
    _inherits = {'hotel.virtual.room': 'openerp_id'}
    _description = 'WuBook Room'

    backend_id = fields.Many2one(comodel_name='wubook.backend', string='Wubook Backend', required=True, ondelete='restrict')
    openerp_id = fields.Many2one(comodel_name='hotel.virtual.room', string='Room', required=True, ondelete='cascade')
    wubook_id = fields.Char(string='ID on WuBook')  # fields.char because 0 is a valid Magento ID
    sync_date = fields.Datetime(string='Last synchronization date')
    #magento_order_id = fields.Many2one(comodel_name='magento.sale.order', string='Magento Sale Order', ondelete='set null')
    # we can also store additional data related to the Magento Invoice


@on_record_create(model_names='wubook.hotel.virtual.room')
def delay_create_room(session, model_name, record_id):
    """
    Delay the job to export the magento invoice.
    """
    create_room.delay(session, model_name, record_id)


@job
def create_room(session, model_name, record_id):
    room = session.env[model_name].browse(record_id)
    user_r = session.env['res.users'].browse(session.env.uid)

    user = user_r.partner_id.wubook_user
    passwd = user_r.partner_id.wubook_passwd
    pkey = user_r.company_id.wubook_pkey
    lcode = user_r.partner_id.wubook_lcode
    wserver = user_r.company_id.wubook_server

    backend_id = room.backend_id.id
    env = get_environment(session, model_name, backend_id)
    room_sync = env.get_connector_unit(RoomSynchronizer)
    return room_sync.run(record_id, wserver, user, passwd, lcode, pkey)

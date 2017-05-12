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
from openerp import api, fields, models
import xmlrpclib

class WuBook(models.TransientModel):
    _name = 'wubook'
    
    
    @api.multi    
    def create_room(self, room_id):
        user_id = self.env['res.users'].browser([self.uid])
        user_id.partner_id.wubook_passwd
        
        wServer = xmlrpclib.Server(user_id.company_id.wubook_server)
        res, tok = wServer.acquire_token(
                user_id.partner_id.wubook_user,
                user_id.partner_id.wubook_passwd,
                user_id.company_id.wubook_pkey)
        
        res, rid = wServer.new_room(
            tok,
            user_id.partner_id.wubook_lcode,
            0,
            room_id.name,
            room_id.beds,
            room_id.price,
            room_id.avail,
            room_id.shortname,
            room_id.defborad
            )
        
        wServer.release_token(tok)
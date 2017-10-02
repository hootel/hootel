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
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID

# TODO: Use new api
class HotelConfiguration(osv.osv_memory):
    _inherit = 'hotel.config.settings'

    _columns = {
        'divide_rooms_by_capacity': fields.boolean('Divide rooms by capacity'),
        'end_day_week': fields.selection([
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday')
        ], string='End day of week', default='6', required=True),
        'type_move': fields.selection([
            ('normal', 'Normal'),
            ('assisted', 'Assisted'),
            ('allow_invalid', 'Allow Invalid')
        ], string='Reservation move mode', default='normal', required=True)
    }

    def set_divide_rooms_by_capacity(self, cr, uid, ids, context=None):
        divide_rooms_by_capacity = self.browse(cr, uid, ids, context=context).divide_rooms_by_capacity
        return self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'hotel.config.settings', 'divide_rooms_by_capacity', divide_rooms_by_capacity)
    
    def set_end_day_week(self, cr, uid, ids, context=None):
        end_day_week = self.browse(cr, uid, ids, context=context).end_day_week
        return self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'hotel.config.settings', 'end_day_week', end_day_week)

    def set_type_move(self, cr, uid, ids, context=None):
        type_move = self.browse(cr, uid, ids, context=context).type_move
        return self.pool.get('ir.values').set_default(cr, SUPERUSER_ID, 'hotel.config.settings', 'type_move', type_move)

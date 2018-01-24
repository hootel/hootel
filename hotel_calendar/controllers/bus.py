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
from openerp.addons.bus.controllers.main import BusController
from openerp.http import request

HOTEL_BUS_CHANNEL_ID = 'hpublic'


# More info...
# https://github.com/odoo/odoo/commit/092cf33f93830daf5e704b964724bdf8586da8d9
class Controller(BusController):
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            # registry, cr, uid, context = request.registry, request.cr, \
            #                              request.session.uid, request.context
            channels = channels + [(
                request.db,
                'hotel.reservation',
                HOTEL_BUS_CHANNEL_ID
            )]
        return super(Controller, self)._poll(dbname, channels, last, options)

# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
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
from openerp.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
from decimal import Decimal
import datetime
import urllib2
import time


#Duda si meter el numero de plazas ocupadas (adults,children) en este modelo (HotelReservationLine)
#o en el modelo HotelRoomReservationLine. Este es el que se muestra en la lista del formulario de reserva
class HotelReservationLine(models.Model):

    _inherit = "hotel_reservation.line"
    
    adults = fields.Integer('Adults', size=64,help='List of adults there in guest list.')
    children = fields.Integer('Children', size=64,help='List of adults there in guest list.')
    
    
    
    
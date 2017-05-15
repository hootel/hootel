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
from dateutil.relativedelta import relativedelta
import datetime
import urllib2
import time

COLOR_TYPES = {'pre-reservation':'#A4A4A4',
               'reservation':'#0000FF',
               'stay':'#FF00BF',
	       'checkout':'#01DF01',
               'dontsell':'#000000',
	       'staff':'#FF4000',
               'directsale':'#8A084B'}


class HotelReservation(models.Model):

    _inherit = "hotel.reservation"   		
		

    @api.depends('state', 'reservation_type')
    def _compute_color(self):
	
	now_str = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
	for rec in self:
		now_date = datetime.datetime.strptime(now_str,
	                                      DEFAULT_SERVER_DATETIME_FORMAT)
		checkin_date = (datetime.datetime.strptime
			            (rec.checkin,
			             DEFAULT_SERVER_DATETIME_FORMAT))
		difference_checkin = relativedelta(now_date, checkin_date)
		checkout_date = (datetime.datetime.strptime
			            (rec.checkout,
			             DEFAULT_SERVER_DATETIME_FORMAT))
		difference_checkout = relativedelta(now_date, checkout_date)
		if rec.state == 'draft':
			rec.reserve_color = COLOR_TYPES.get('pre-reservation')
		elif rec.reservation_type == 'reservation':
			rec.reserve_color = COLOR_TYPES.get('reservation')
		elif rec.reservation_type == 'staff':
			rec.reserve_color = COLOR_TYPES.get('staff')
		elif rec.reservation_type == 'out':
			rec.reserve_color = COLOR_TYPES.get('dontsell')
		elif rec.state == 'checkin' and difference_checkout.days == 0:
			rec.reserve_color = COLOR_TYPES.get('checkout')
		else:
			rec.reserve_color = "#FFF"
	
    to_assign = fields.Boolean('To Assign')
    reservation_type = fields.Selection([('normal', 'Normal'), ('staff', 'Staff'),
                              ('out', 'Out of Service')],
                             'Reservation Type',
                             default=lambda *a: 'normal')
    out_service_description = fields.Text('Cause of out of service')
    reserve_color = fields.Char(compute='_compute_color',string='Color', store=True)
    
    
    
			
	
	
		


    
    

    

# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2020 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
from datetime import datetime
from odoo import api, fields, models
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class DoorCodeWizard(models.TransientModel):
    _name = 'door_code'

    @api.model
    def _get_default_date_start(self):
        return datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

    date_start = fields.Date("Start of the period",
                             default=_get_default_date_start)
    date_end = fields.Date("End of period",
                           default=_get_default_date_start)
    door_code = fields.Html('Door codes')

    @api.multi
    def check_code(self):
        reservation = self.env['hotel.reservation']
        codes = reservation.door_codes_text(self.date_start, self.date_end)
        return self.write({
             'door_code': codes
             })

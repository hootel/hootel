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
from openerp import models, fields, api


class MassivePriceChangeWizard(models.TransientModel):
    _name = 'hotel.wizard.massive.price.reservation.days'

    new_price = fields.Float('New Price', default=1, min=1)

    @api.multi
    def massive_price_change_days(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation_id = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        reservation_id.reservation_lines.write({
            'price': self.new_price,
        })

        return True

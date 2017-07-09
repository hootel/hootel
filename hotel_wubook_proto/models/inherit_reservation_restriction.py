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
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class ReservationRestriction(models.Model):
    _inherit = 'reservation.restriction'

    wpid = fields.Char("WuBook Plan ID", readonly=True)

    @api.multi
    def get_wubook_restrictions(self):
        self.ensure_one()
        prices = {}
        min_date = False
        max_date = False
        for item in self.item_ids:
            if not item.date_start or not item.date_end:
                continue
            date_start_dt = fields.Datetime.from_string(item.date_start)
            date_end_dt = fields.Datetime.from_string(item.date_end)
            if not min_date or date_start_dt < min_date:
                min_date = date_start_dt
            if not max_date or date_end_dt > max_date:
                max_date = date_end_dt
        if not min_date or not max_date:
            return prices
        days_diff = abs((max_date - min_date).days)
        vrooms = self.env['hotel.virtual.room'].search([('wrid', '!=', 'none')])
        for vroom in vrooms:
            prices.update({vroom.wrid: []})
            for i in range(0, days_diff or 1):
                ndate_dt = min_date + timedelta(days=i)
                product_id = vroom.product_id.with_context(
                    quantity=1,
                    date=ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    pricelist=self.id,
                    uom=vroom.product_id.product_tmpl_id.uom_id.id)
                prices[vroom.wrid].append(product_id.price)
        return prices

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True):
            wpid = self.env['wubook'].create_rplan(vals['name'])
            vals.update({'wpid': wpid})
        restriction = super(ReservationRestriction, self).create(vals)

        rules = self._context.get('rules')
        if rules:
            # Basic Rules
            self.env['reservation.restriction.item'].with_context({'wubook_action': False}).create({
                'closed_arrival': rules['closed_arrival'],
                'closed': rules['closed'],
                'min_stay': rules['min_stay'],
                'closed_departure': rules['closed_departure'],
                'max_stay': rules['max_stay'],
                'min_stay_arrival': rules['min_stay_arrival'],
                'restriction_id': restriction.id,
                'applied_on': '1_global',
            })

        return restriction

    @api.multi
    def write(self, vals):
        nname = vals.get('name')
        if self._context.get('wubook_action', True) and nname:
            for record in self:
                self.env['wubook'].update_rplan_name(vals.get('wpid', record.wpid),
                                                     nname)
        updated = super(ReservationRestriction, self).write(vals)
        return updated

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True):
            for record in self:
                self.env['wubook'].delete_rplan(record.wpid)
        return super(ReservationRestriction, self).unlink()

    @api.multi
    def import_restriction_plans(self):
        self.env['wubook'].get_restriction_plans()
        return True

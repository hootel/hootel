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
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
from openerp import models, fields, api
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo.addons.hotel import date_utils
import logging
_logger = logging.getLogger(__name__)


class SplitReservationWizard(models.TransientModel):
    _name = 'hotel.wizard.split.reservation'

    nights = fields.Integer('Nights', default=1, min=1)

    @api.multi
    def split_reservation(self):
        reservation_id = self.env['hotel.reservation'].browse(
                                            self.env.context.get('active_id'))
        if reservation_id:
            date_start_dt = date_utils.get_datetime(reservation_id.checkin)
            date_end_dt = date_utils.get_datetime(reservation_id.checkout)
            date_diff = date_utils.date_diff(date_start_dt, date_end_dt,
                                             hours=False)
            for record in self:
                new_start_date_dt = date_start_dt + \
                                    timedelta(days=date_diff-record.nights)
                if record.nights >= date_diff or record.nights < 1:
                    raise ValidationError("Invalid Nights! Max is \
                                            '%d'" % (date_diff-1))

                vals = reservation_id.generate_copy_values(
                    new_start_date_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    date_end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                )
                # Days Price
                reservation_lines = [[], []]
                tprice = [0.0, 0.0]
                div_dt = date_utils.dt_no_hours(new_start_date_dt)
                for rline in reservation_id.reservation_lines:
                    rline_dt = date_utils.get_datetime(rline.date, hours=False)
                    _logger.info("----AAAAAA")
                    _logger.info(rline_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                    _logger.info(div_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                    if rline_dt >= div_dt:
                        reservation_lines[1].append((0, False, {
                            'date': rline.date,
                            'price': rline.price
                        }))
                        _logger.info("PASA AAA")
                        _logger.info(reservation_lines[1])
                        tprice[1] += rline.price
                        reservation_lines[0].append((2, rline.id, False))
                    else:
                        tprice[0] += rline.price

                reservation_id.write({
                    'checkout': new_start_date_dt.strftime(
                                            DEFAULT_SERVER_DATETIME_FORMAT),
                    'price_unit': tprice[0],
                    'reservation_lines': reservation_lines[0],
                    'splitted': True,
                })
                parent_res = reservation_id.parent_reservation or \
                    reservation_id
                _logger.info("PASA BBB")
                _logger.info(reservation_lines[1])
                vals.update({
                    'splitted': True,
                    'price_unit': tprice[1],
                    'reservation_lines': reservation_lines[1],
                    'parent_reservation': parent_res.id,
                })
                reservation_copy = self.env['hotel.reservation'].create(vals)
                if not reservation_copy:
                    raise ValidationError("Unexpected error copying record. \
                                            Can't split reservation!")
            # return {
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'hotel.folio',
            #     'views': [[False, "form"]],
            #     'target': 'new',
            #     'res_id': reservation_id.folio_id.id,
            # }
        return True

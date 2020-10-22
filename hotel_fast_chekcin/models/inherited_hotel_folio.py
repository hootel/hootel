# Copyright 2020 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'

    hide_pay = fields.Boolean("Show price for payment",
                              default=True,
                              help='Hide or show the price in external tools (Fast Checkin, Cashiers, etc.)')

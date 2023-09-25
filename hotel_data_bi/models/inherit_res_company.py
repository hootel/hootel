# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    # def _odoo_url_v2(self):
    #     config = self.env['ir.config_parameter'].sudo(
    #     ).get_param('web.base.url', "Blanco")
    #     config = config.split('/')[2]
    #     return config

    id_hotel = fields.Integer(
        'Unique ID for DataBI', default=0,
        help='It must be unique to be able to identify the hotel, \
        within a hotel group.')
    expedia_rate = fields.Integer(
        'Expedia Rate DataBI',
        default=18, required=True, digits=(2),
        help='It is the commission percentage negotiated with the \
        Expedia company, expressed with two digits. \
        Example: 18 = 18% commission.')
    data_bi_days = fields.Integer(
        'Days to download',
        default=60, required=True, digits=(3),
        help='Number of days, which are downloaded data, \
        backwards, by default are 60 days to download.')
    json_reservations_v3_data = fields.Text(
        string="Json from V3 reservations")
    json_outs_v3_data = fields.Text(
        string="Json from V3 Out")

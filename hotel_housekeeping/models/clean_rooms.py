# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class Clean_rooms(models.Model):

    # @api.multi
    @api.depends('state')
    def _check_color(self):
        for record in self:
            color = '#ffffff'
            k_color = 1
            if record.state == 2:
                color = '#f8c5c5'
            elif record.state == 3:
                color = '#f8f6c5'
            elif record.state == 4:
                color = '#dcf8c5'
            elif record.state == 5:
                color = '#a2fba7'
            elif record.state == 6:
                color = '#f6d3fa'
            if record.type == 1:
                k_color = 1
            elif record.type == 2:
                k_color = 2
            elif record.type == 3:
                k_color = 3
            elif record.type == 4:
                k_color = 4
            elif record.type == 5:
                k_color = 5
            record.update({'color_state': color, 'color_type': k_color})

    _name = 'clean_rooms'
    _description = 'Clean Rooms'

    date = fields.Date('Date', required=True,)
    room_id = fields.Many2one('hotel.room', 'Hotel Room', required=True,)
    comment = fields.Text(string='Cleaning Room Notes')
    type = fields.Selection([(1, 'Exit'), (2, 'Client'), (3, 'Review'),
                             (4, 'Staff'), (5, 'Out of order')],
                            string='Clean as...')
    state = fields.Selection([(1, 'Cleaned'), (2, 'Dirty'), (3, 'Cleaning'),
                              (4, 'Declined'), (5, 'Ecologic'), (6, 'Staff')],
                             string='State')
    clean_start = fields.Datetime('Start cleaning')
    clean_end = fields.Datetime('End cleaning')
    housekeeper = fields.Many2one('res.users', 'Assigned housekeeper')
    reservation = fields.Many2one('hotel.reservation.line', 'Reservation')
    color_state = fields.Char(string='Color State', compute='_check_color')
    color_type = fields.Integer(string='Color Type', compute='_check_color')

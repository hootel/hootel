# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class Clean_rooms(models.Model):

    _name = 'clean_rooms'
    _description = 'Clean Rooms'

    # Fields declaration
    room_id = fields.Many2one(
        'hotel.room',
        string='Hotel Room',
        required=True,)
    housekeeper_id = fields.Many2one(
        'res.users',
        string='Assigned housekeeper')  # REVIEW hr_employed?
    reservation_id = fields.Many2one(
        'hotel.reservation.line',
        string='Reservation')
    # REVIEW Change date and start/end by datetime start anda datetime end?
    date = fields.Date('Date', required=True,)
    clean_start = fields.Datetime('Start cleaning')
    clean_end = fields.Datetime('End cleaning')
    comment = fields.Text(string='Cleaning Room Notes')
    type = fields.Selection([
        ('exit', 'Exit'),
        ('client', 'Client'),
        ('review', 'Review'),
        ('staff', 'Staff'),
        ('out', 'Out of order')],
        string='Clean as...')
    from_state = fields.Selection([
        ('cleaned', 'Cleaned'),
        ('dirty', 'Dirty'),
        ('cleaning', 'Cleaning'),
        ('declined', 'Declined'),
        ('ecologic', 'Ecologic'),
        ('staff', 'Staff'),
        ('cleaned_ok', 'Cleaned OK')],  # REVIEW Change 'cleaned OK' by flow
        string='State',
        compute='_compute_from_state',
        compute_sudo=True,
        # REVIEW inverse='_set_cleaned_log', --is useful?
        search='_search_from_room_state')
    color_state = fields.Char(string='Color State',
                              compute='_check_color')
    color_type = fields.Integer(string='Color Type',  # REVIEW Is necesary?
                                compute='_check_color')  # REVIEW Is necesary?

    # Compute and Search methods
    @api.multi
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
            record.update({
                'color_state': color,
                'color_type': k_color
                })

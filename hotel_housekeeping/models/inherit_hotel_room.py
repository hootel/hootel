# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HotelRoom(models.Model):

    _inherit = 'hotel.room'

    # Fields declaration
    default_housekeeper_id = fields.Many2one(
        'res.users',
        'Assigned housekeeper')  # REVIEW hr_employed? is necesary in room?
    # REVIEW clean_type is necesary in room model?
    clean_type = fields.Selection([
        ('exit', 'Exit'),
        ('client', 'Client'),
        ('review', 'Review'),
        ('staff', 'Staff'),
        ('out', 'Out of order')],
        string='Clean as...')
    clean_state = fields.Selection([
        ('cleaned', 'Cleaned'),
        ('dirty', 'Dirty'),
        ('cleaning', 'Cleaning'),
        ('declined', 'Declined'),
        ('ecologic', 'Ecologic'),
        ('staff', 'Staff'),
        ('cleaned_ok', 'Cleaned OK')],  # REVIEW Change 'cleaned OK' by flow
        string='State',
        compute='_compute_state',
        compute_sudo=True,
        # REVIEW inverse='_set_cleaned_log', --is useful?
        search='_search_room_state')
    clean_notes = fields.Text('Notes')

    # Compute and Search methods
    @api.multi
    def _compute_state(self):
        for room in self:
            return False
            # TODO

    def _search_room_state(self, operator, value):
        # TODO Build domain to return search Example: [('id', 'in', ..)]
        return [('id', 'in', False)]

    # Action methods
    @api.multi
    def rack_form_action(self):
        view_id = self.env.ref('hotel_housekeeping.rack_rooms_form_view').id
        context = self._context.copy()
        return {
            'name': 'rack_rooms_form_view',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hotel.room',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'action': 'edit',
            'context': context,
        }

    @api.multi
    def view_reservation_action(self):
        view_id = self.env.ref('hotel.hotel_reservation_view_form').id
        context = self._context.copy()
        res_id = self.re_line_now.reservation_id.id
        return {
            'name': 'rack_rooms_form_view',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hotel.reservation',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': res_id,
            'context': context,
        }

    @api.multi
    def action_save(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

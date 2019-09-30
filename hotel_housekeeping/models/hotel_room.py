# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class HotelRoom(models.Model):

    _inherit = 'hotel.room'

    housekeeper = fields.Many2one('res.users', 'Assigned housekeeper')
    re_line_now = fields.Many2one('hotel.reservation.line', 'Reservation')
    clean_type = fields.Selection([(1, 'Exit'), (2, 'Client'), (3, 'Review'),
                                   (4, 'Staff'), (5, 'Out of order')],
                                  string='Clean as...')
    clean_state = fields.Selection([(1, 'Cleaned'), (2, 'Dirty'),
                                    (3, 'Cleaning'), (4, 'Declined'),
                                    (5, 'Ecologic'), (6, 'Staff'),
                                    (7, 'Cleaned OK')],
                                   string='State')
    clean_notes = fields.Text('Notes')

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

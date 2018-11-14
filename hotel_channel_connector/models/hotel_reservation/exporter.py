# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api, _

class HotelReservationExporter(Component):
    _name = 'channel.hotel.reservation.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.exporter'

    @api.model
    def cancel_reservation(self, binding):
        user = self.env['res.user'].browse(self.env.uid)
        return self.backend_adapter.cancel_reservation(
            binding.external_id,
            _('Cancelled by %s') % user.partner_id.name)

    @api.model
    def mark_booking(self, binding):
        return self.backend_adapter.mark_bookings([binding.external_id])

    @api.model
    def mark_bookings(self, external_ids):
        return self.backend_adapter.mark_bookings(external_ids)

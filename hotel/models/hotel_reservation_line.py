# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class HotelReservationLine(models.Model):
    _name = "hotel.reservation.line"
    _order = "date"

    @api.multi
    def name_get(self):
        result = []
        for res in self:
            date = fields.Date.from_string(res.date)
            name = u'%s/%s' % (date.day, date.month)
            result.append((res.id, name))
        return result

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation',
                                     ondelete='cascade', required=True,
                                     copy=False)
    date = fields.Date('Date')
    state = fields.Selection(related='reservation_id.state', store="True",
                             readonly=True)
    price = fields.Float(
        string='Price',
        digits=dp.get_precision('Product Price'))
    cancel_discount = fields.Float(
        string='Cancel Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    invoice_line_ids = fields.Many2many(
        'account.invoice.line',
        'reservation_line_invoice_rel',
        'reservation_line_id', 'invoice_line_id',
        string='Invoice Lines', readonly=True, copy=False)
    room_id = fields.Many2one(related='reservation_id.room_id', store="True",
                              readonly=True)
    is_automatic_blocked = fields.Boolean(related='reservation_id.is_automatic_blocked', store="True",
                              readonly=True)

    @api.constrains('date')
    def constrain_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and
                r.id != record.id
            )
            if duplicated:
                raise ValidationError(_('Duplicated reservation line date'))

    #@api.constrains('state')
    #def constrain_service_cancel(self):
    #    for record in self:
    #        if record.state == 'cancelled':
    #            room_services = record.reservation_id.service_ids
    #            for service in room_services:
    #                cancel_lines = service.service_line_ids.filtered(
    #                    lambda r: r.date == record.date
    #                )
    #                cancel_lines.day_qty = 0

    def unlink(self):
        for record in self:
            if record.is_automatic_blocked:
                return
            room = record.room_id
            date = record.date
            active = False
            self._compute_rooms_beds_equivalents(room, date, active)
        super(HotelReservationLine, self).unlink()

    def create(self, vals):
        if self.env.context.get('blocked', False):
            return super(HotelReservationLine, self).create(vals)
        room = self.env['hotel.reservation'].browse(vals['reservation_id']).room_id
        date = vals['date']
        active = True
        self._compute_rooms_beds_equivalents(room, date, active)
        return super(HotelReservationLine, self).create(vals)

    @api.model
    def _compute_rooms_beds_equivalents(self, room, date, active):
        if room and date and room.shared_room_id:
            shared_room = room.shared_room_id
            equivalent_room = shared_room.equivalent_room_id
            if equivalent_room:
                shared_room.room_equivalent_out(date, active)
            shared_beds = self.env['hotel.shared.room'].search([
                ('equivalent_room_id', '=', room.id)
            ])
            if shared_beds:
                shared_beds.beds_out(date, active)

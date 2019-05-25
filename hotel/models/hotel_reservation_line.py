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

    def _default_line_state(self):
        return self.reservation_id.state

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation',
                                     ondelete='cascade', required=True,
                                     copy=False)
    date = fields.Date('Date', index=True)
    state = fields.Selection([
        ('draft', 'Pre-reservation'),
        ('confirm', 'Pending Entry'),
        ('booking', 'On Board'),
        ('done', 'Out'),
        ('cancelled', 'Cancelled')
        ],string='State', readonly=True,
        default=_default_line_state, copy=False,
        track_visibility='onchange')
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

    @api.constrains('date')
    def constrains_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and
                r.id != record.id
            )
            if duplicated:
                raise ValidationError(_('Duplicated reservation line date'))

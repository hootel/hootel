# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError
from openerp.tools.translate import _
import logging
_logger=logging.getLogger(__name__)


class Wizard(models.TransientModel):
    _name = 'checkin.wizard'

    def default_enter_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.checkin
        if 'enter_date' in self.env.context:
            return self.env.context['enter_date']
        return False

    def default_exit_date(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.checkout
        if 'exit_date' in self.env.context:
            return self.env.context['exit_date']
        return False

    def default_reservation_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation
        if 'reserva_id' in self.env.context:
            return self.env.context['reserva_id']
        return False

    def default_partner_id(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.partner_id
        if 'partner_id' in self.env.context:
            return self.env.context['partner_id']
        return False

    def default_cardex_ids(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.cardex_ids

    def default_count_cardex(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.cardex_count

    def default_pending_cardex(self):
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.adults + reservation.children - reservation.cardex_count

    def comp_checkin_list_visible(self):
        if 'partner_id' in self.env.context:
            self.list_checkin_cardex = False
        return

    def comp_checkin_edit(self):
        if 'edit_cardex' in self.env.context:
            return True
        return False

    cardex_ids = fields.Many2many('cardex', 'reservation_id', default=default_cardex_ids)
    count_cardex = fields.Integer('Cardex counter', default=default_count_cardex)
    pending_cardex = fields.Integer('Cardex pending', default=default_pending_cardex)
    partner_id = fields.Many2one('res.partner', default=default_partner_id)
    reservation_id = fields.Many2one('hotel.reservation', default=default_reservation_id)
    enter_date = fields.Date( default=default_enter_date, required=True)
    exit_date = fields.Date( default=default_exit_date, required=True)
    email_cardex = fields.Char('E-mail', related='partner_id.email')
    mobile_cardex = fields.Char('Mobile', related='partner_id.mobile', store=True)
    list_checkin_cardex = fields.Boolean(compute=comp_checkin_list_visible, default=True, store=True)
    edit_checkin_cardex = fields.Boolean(default=comp_checkin_edit, store=True)

    # you can use @api.multi for collection processing like this:
    # for ticket in self: ...something do here
    # or you can use @api.model for processing only one object
    @api.multi
    def action_save_check(self):
        cardex_val={
          'partner_id':self.partner_id.id,
          'enter_date':self.enter_date,
          'exit_date':self.exit_date}
        record_id = self.env['hotel.reservation'].browse(self.reservation_id.id)
        record_id.write({
           'cardex_ids':[(0,False,cardex_val)]})
        if record_id.cardex_count > 0:
            record_id.state = 'booking'
            record_id.is_checkin = False
            folio = self.env['hotel.folio'].browse(self.reservation_id.folio_id.id)
            folio.checkins_reservations -= 1
        return

    @api.multi
    def action_update_check(self):
        record_id = self.env['hotel.reservation'].browse(self.reservation_id.id)
        record_id.write({
          'partner_id':self.partner_id.id,
          'enter_date':self.enter_date,
          'exit_date':self.exit_date})
        return {'type': 'ir.actions.act_window_close'}

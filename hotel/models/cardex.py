#-*- coding: utf-8 -*- 

from openerp import models, fields, api
from openerp.exceptions import except_orm, ValidationError
import datetime

class Cardex(models.Model):
    _name = 'cardex'

    # Validation for Departure date is after arrival date.
    @api.constrains('exit_date')
    def validation_dates(self):
        if self.exit_date < self.enter_date:
             raise models.ValidationError('Departure date (%s) is prior to arrival on %s' % (self.exit_date, self.enter_date))

    def default_reservation_id(self):        
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation
        return False

    def default_enter_date(self):        
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.checkin
        return False

    def default_exit_date(self):        
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.checkout
        return False

    def default_partner_id(self):        
        if 'reservation_id' in self.env.context:
            reservation = self.env['hotel.reservation'].search([('id','=',self.env.context['reservation_id'])])
            return reservation.partner_id
        return False

    @api.onchange('enter_date', 'exit_date') # if these fields are changed, call method
    def check_change_dates(self):
        if self.exit_date <= self.enter_date:
            date_1 = datetime.datetime.strptime(self.enter_date, "%Y-%m-%d")
            date_2 = date_1 + datetime.timedelta(days=1)
            self.update({'exit_date':date_2,})
            raise ValidationError('Departure date, is prior to arrival. Check it now. %s' %(date_2))

    partner_id = fields.Many2one('res.partner', default=default_partner_id)
    reservation_id = fields.Many2one('hotel.reservation', default=default_reservation_id, readonly=True)
    enter_date = fields.Date( default=default_enter_date, required=True)
    exit_date = fields.Date( default=default_exit_date, required=True)
# Copyright 2020-2021 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import timedelta
import logging
_logger = logging.getLogger(__name__)


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'

    hide_pay = fields.Boolean("Show price for payment",
                              default=True,
                              help='Hide or show the price in external tools (Fast Checkin, Cashiers, etc.)')

    fc_mail_sended = fields.Datetime(string="F-C email sent",
                                     required=False)
    fc_visits = fields.Integer(string="F-C Visits",
                               required=False,
                               default=0)
    fc_counts = fields.Integer(string="F-C Writed",
                               required=False,
                               default=0)

    @api.model
    def fast_checkin_mailer(self):
        """
        This method is for send reminder mails
        """
        reservations = self.env['hotel.reservation'].search([
            ('folio_id.checkin_partner_pending_count', '>', 0),
            # ('checkin', '>', fields.Date.today()),
            # ('checkin', '<', fields.Date.from_string(fields.Date.today()) + timedelta(days=8)),
            ('checkin', '=', fields.Date.from_string(fields.Date.today()) + timedelta(days=1)),
            ('state', '=', 'confirm'),
            ('folio_id.state', '=', 'confirm'),
            ('folio_id.partner_id.email', '!=', False),
        ])

        folios = reservations.mapped('folio_id')

        for folio in folios:
            folio.send_fast_checkin_mail()
        return

    @api.model
    def fast_checkin_view_mail(self):
        self.ensure_one()
        template = self.env.ref(
            'hotel_fast_chekcin.mail_template_checkin_reminder',
            False,
        )
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form',
            False,
        )
        ctx = dict(
            default_model='hotel.folio',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            user_id=self.env.user.id,
        )
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def send_fast_checkin_mail(self):
        if self.fc_mail_sended:
            if self.room_lines[0].checkin == fields.Date.from_string(
                 fields.Datetime.now()) + timedelta(days=1):
                if (fields.Date.from_string(self.fc_mail_sended) + timedelta(days=2) >
                        fields.Date.from_string(fields.Datetime.now())):
                    _logger.warning('Fast-Checkin Sending MAIL 48 hours restrict problem %s',
                                    self.name)
                return
            else:
                return

        self.env.ref('hotel_fast_chekcin.mail_template_checkin_reminder').send_mail(
            self.id,
            force_send=True)
        self.fc_mail_sended = fields.Datetime.now()

        msg = "<strong>Fast-Checkin</strong></br> "
        msg += "Mail enviado a</br> " + self.partner_id.email
        self.message_post(body=msg, subject='Fast Checkin System')

        _logger.info('Fast-Checkin Sending MAIL to %s', self.name)
        return

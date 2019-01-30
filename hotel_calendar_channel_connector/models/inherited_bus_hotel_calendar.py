# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, api
from odoo.addons.hotel_calendar.controllers.bus import HOTEL_BUS_CHANNEL_ID


class BusHotelCalendar(models.TransientModel):
    _inherit = 'bus.hotel.calendar'

    @api.model
    def _generate_availability_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'availability',
            'availability': {
                vals['room_type_id']: {
                    date_dt.strftime("%d/%m/%Y"): {
                        'quota': vals['quota'],
                        'max_avail': vals['max_avail'],
                        'id': vals['id'],
                        'no_ota': vals['no_ota'],
                    },
                },
            },
        }

    @api.model
    def send_availability_notification(self, vals):
        notif = self._generate_availability_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def _generate_issue_notification(self, ntype, title, issue_id, section,
                                     message):
        user_id = self.env['res.users'].browse(self.env.uid)
        return {
            'type': 'issue',
            'subtype': ntype,
            'title': title,
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'issue': {
                'issue_id': issue_id,
                'section': section.upper(),
                'message': message,
            },
        }

    @api.model
    def send_issue_notification(self, ntype, title, issue_id, section, message):
        notif = self._generate_issue_notification(ntype, title, issue_id, section, message)
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'hotel.reservation',
             HOTEL_BUS_CHANNEL_ID), notif)

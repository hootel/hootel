# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta
from dateutil import tz
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from ..scrapers import scraper_abc
import logging
_logger = logging.getLogger(__name__)

CALENDAR_EVENT_TYPE_CONCERT = 'Concert'
REQUEST_DELAY = 3
MONTHS_MAP = {
    'Enero': 1,
    'Febrero': 2,
    'Marzo': 3,
    'Abril': 4,
    'Mayo': 5,
    'Junio': 6,
    'Julio': 7,
    'Agosto': 8,
    'Septiembre': 9,
    'Octubre': 10,
    'Noviembre': 11,
    'Diciembre': 12,
}


class EventCity:
    def __init__(self, postid=0, city='', dates=[], name='', address='',
                 venue='', prices='', buy_tickets=''):
        self.postid = postid
        self.city = city
        self.dates = dates
        self.name = name
        self.address = address
        self.venue = venue
        self.prices = prices
        self.buy_tickets = buy_tickets


class ImportEventsWizard(models.TransientModel):
    _name = 'wizard.import.events'

    @api.model
    def _get_default_year(self):
        return datetime.now().year

    city = fields.Char('City', required=True)
    year = fields.Char('Year', required=True, default=_get_default_year)

    @api.multi
    def import_events(self):
        events = []
        scraper_abc._import_city_events(
            events,
            '%s %s' % (self.city, self.year),
            pags=1,
            onlyFuture=True)

        cal_event_obj = self.env['calendar.event']
        event_type = self.env['calendar.event.type'].search([
            ('name', '=', CALENDAR_EVENT_TYPE_CONCERT)
        ], limit=1)
        for event in events:
            fev = cal_event_obj.search([
                ('web_id', '=', event.postid),
            ])
            if fev:
                fev.unlink()
            for day in event.dates:
                day = day.replace(tzinfo=tz.gettz('Europe/Madrid'))
                day_utc = day.astimezone(tz.gettz('UTC'))
                vals = {
                    'name': event.name,
                    'location': "%s, %s" % (event.address, event.venue),
                    'description': _("Price: %s\nBuy Tickets: %s") % (
                        event.prices,
                        event.buy_tickets),
                    'allday': False,
                    'state': 'open',
                    'privacy': 'confidential',
                    'categ_ids': [(6, 0, [event_type.id])] if event_type else [],
                    'web_id': event.postid,
                    'start': day_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'stop': (day_utc + timedelta(hours=2)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'duration': 2.0,
                }
                cal_event_obj.with_context(no_mail_to_attendees=True).create(vals)
        return True

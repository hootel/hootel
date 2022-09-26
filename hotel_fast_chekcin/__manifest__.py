# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-2021 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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

{
    'name': 'Hotel Fast Checkin',
    'version': '2.4',
    'author': "Jose Luis Algara Toledo <osotranquilo@gmail.com>",
    'website': 'https://www.aldahotels.com',
    'category': 'hotel fast checkin',
    'summary': "Module for connecting Odoo with the Fast Checkin application \
                made in Django.",
    'description': "Hotel Fast Checkin",
    'depends': [
        'hotel', 'hotel_l10n_es'
    ],
    'data': [
        'views/inherit_res_company.xml',
        'views/inherit_hotel_reservation.xml',
        'views/inherit_hotel_folio.xml',
        'data/cron_jobs.xml',
        'data/mail_template_checkin_reminder.xml',
    ],
    'qweb': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

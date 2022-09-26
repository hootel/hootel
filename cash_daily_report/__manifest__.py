# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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
    'name': 'Cash Daily Report',
    'version': '1.0',
    'author': "Alexandre Díaz <dev@redneboa.es>",
    'website': 'https://www.eiqui.com',
    'category': 'reports',
    'summary': "Export payments report in xls format",
    'description': "Cash Daily Report",
    'depends': [
        'account',
        'account_payment_return',
        'hotel',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter']
    },
    'data': [
        'wizard/cash_daily_report.xml',
        'views/inherited_account_payment_views.xml',
        'views/inherited_payment_return_views.xml',
        'data/menus.xml',
        'data/cron_jobs.xml',
    ],
    'qweb': [],
    'test': [
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

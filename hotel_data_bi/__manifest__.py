# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
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
    'name': 'Hotel MyDataBI Exporter',
    'version': '1.1',
    'author': "Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>",
    'website': 'https://www.aldahotels.com',
    'category': 'hotel/revenue',
    'summary': "Revenue system and export reservation Data to MyDataBI",
    'description': """
    Revenue MyDataBI Exporter

    To use this module you need to:

    Create a user and give the 'Hotel Management/Export data BI' permission.
    """,
    'depends': ['hotel', 'hotel_l10n_es'],
    'data': [
        'views/data_bi.xml',
        'views/inherit_res_company.xml',
        'security/data_bi.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

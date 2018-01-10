# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Alda Hotels <informatica@aldahotels.com>
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
    'name': 'Hotel l10n_es',
    'version': '9.0.0.3',
    'author': "Jose Luis Algara",
    'website': "http://www.aldahotels.com",
    'category': 'Hotel',
    'summary': "",
    'description': "",
    'depends': [
        'hotel',
        'partner_contact_gender',
        'partner_contact_birthdate',
        'partner_firstname',
    ],
   'data': [
        'data/code_ine.csv',
        'data/category.csv',
        'data/report_viajero_paperformat.xml',
        'report/report_parte_viajero.xml',
        'views/report_viajero.xml',
        'wizard/policewizard.xml',
        'wizard/inewizard.xml',
        'wizard/inherit_checkinwizard.xml',
        'views/cardex_partner.xml',
        'views/category.xml',
        'views/code_ine.xml',
        'views/inherit_res_company.xml',
        'views/report_viajero.xml',
        'views/inherit_cardex.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

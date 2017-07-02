# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
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
    'name': 'Hotel WuBook Prototype',
    'version': '1.0',
    'author': "Alexandre Díaz (Aloxa Solucións S.L.) <alex@aloxa.eu>",
    'website': 'https://www.eiqui.com',
    'category': 'eiqui/hotel',
    'summary': "Hotel WuBook",
    'description': "Hotel WuBook Prototype",
    'depends': [
        'hotel',
        'pricelist_week',
    ],
    'external_dependencies': {
        'python': ['xmlrpclib']
    },
    'data': [
        #'data/cron_jobs.xml',
        'wizards/wubook_installer.xml',
        'wizards/wubook_import_plan_prices.xml',
        'views/general.xml',
        'views/res_config.xml',
        'views/inherit_hotel_reservation.xml',
        'views/inherit_hotel_virtual_room.xml',
        'views/inherit_hotel_folio.xml',
        'views/inherit_product_pricelist.xml',
        'views/inherit_product_pricelist_item.xml',
        'views/wubook_channel_info.xml',
        'data/menus.xml',
        'data/sequences.xml',
        #'views/res_config.xml'
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

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
    'name': 'Hotel Reservation Advance',
    'version': '1.0',
    'author': "Alexandre Díaz (Aloxa Solucións S.L.) <alex@aloxa.eu>, Darío Lodeiros (Aloxa Solucións S.L.) <dario@aloxa.eu>",
    'website': 'http://www.aloxa.eu',
    'category': 'Generic Modules/Hotel Reservation',
    'summary': "Advances Options to Hotel Reservation",
    'description': '''    Shared Rooms.-
    Room to Cleaned.- 
    Virtual Room.-
    Types of reservation.-
    Cancelation policy.-
    Usability Changes.-
    Resenvation to assign.-
    Reservation Restrictions.-
    Signal Payment control.-
    New view calendar reservations.-    
    ''',
    'depends': ['hotel_reservation',
    ],
    'external_dependencies': {
        'python': []
    },
    'data': [
        "views/inherit_account_payment_views.xml",
        "views/inherit_hotel_reservation_views.xml",
        "views/inherit_hotel_room_views.xml",
        "views/inherit_res_company_views.xml",
        "views/reservation_restriction_views.xml",
        "views/virtual_room_views.xml",
        "views/inherit_hotel_folio_views.xml",
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}

# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------

{
    'name': 'Hotel Management',
    'version': '0.07',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA,\
    Odoo Community Association (OCA),\
    Darío Lodeiros,\
    Jose Luis Algara,\
    Alexandre Díaz Cuadrado',
    'images': [],
    'category': 'Generic Modules/Hotel Management',
    'website': 'http://www.serpentcs.com',
    'depends': [
        'sale_stock',
        'report',
        'account_payment_return',
        'cash_daily_report',
    ],
    'license': "",
    'demo': ['data/hotel_data.xml'],
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'wizard/massive_changes.xml',
        'wizard/split_reservation.xml',
        'wizard/duplicate_reservation.xml',
        'views/res_config.xml',
        'data/menus.xml',
        'views/inherit_account_payment_views.xml',
        'views/inherit_account_invoice_views.xml',
        'wizard/hotel_wizard.xml',
        'wizard/checkinwizard.xml',
        'wizard/massive_price_reservation_days.xml',
        'views/hotel_sequence.xml',
        'views/hotel_report.xml',
        'views/report_hotel_management.xml',
        'views/currency_exchange.xml',
        'views/hotel_floor.xml',
        'views/hotel_folio.xml',
        'views/inherit_res_partner.xml',
        'views/hotel_service_type.xml',
        'views/hotel_service_line.xml',
        'views/hotel_room_type.xml',
        'views/hotel_room.xml',
        'views/hotel_service.xml',
        'views/inherit_product_product.xml',
        'views/hotel_room_amenities_type.xml',
        'views/hotel_room_amenities.xml',
        'views/reservation_restriction_views.xml',
        'views/reservation_restriction_item_views.xml',
        'views/hotel_reservation.xml',
        'views/virtual_room_views.xml',
        'views/cardex.xml',
        'views/virtual_room_availability.xml',
        # 'views/hotel_dashboard.xml',
        'views/inherit_web_assets_backend.xml',
        'data/cron_jobs.xml',
        'data/records.xml',
        'data/email_template_cancel.xml',
        'data/email_template_reserv.xml',
        'data/email_template_exit.xml',
    ],
    'qweb': ['static/src/xml/qweb.xml'],
    'css': ['static/src/css/room_kanban.css'],
    'auto_install': False,
    'installable': True
}

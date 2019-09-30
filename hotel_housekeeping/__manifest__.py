# Copyright 2019 Jose Luis Algara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Housekeeping',
    'description': """
        Management of room cleaning and cleaning staff""",
    'summary': "Management housekeeping in Hotel",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>",
    'website': 'www.aldahotels.com',
    'category': 'hotel/housekeeping',
    'depends': ['hotel'],
    'data': [
        'views/hotel_room.xml',
        # 'views/clean_rooms.xml',
        'security/groups.xml',
        'security/clean_rooms.xml',
        'report/housekeeping_report.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

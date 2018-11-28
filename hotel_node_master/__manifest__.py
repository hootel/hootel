{
    'name': 'Hotel Node Master',
    'summary': """Provides centralized hotel management features""",
    'version': '0.1.0',
    'author': 'Pablo Q. Barriuso, \
               Darío Lodeiros, \
               Alexandre Díaz, \
               Odoo Community Association (OCA)',
    'category': 'Generic Modules/Hotel Management',
    'depends': [
        'project',
        'connector'
    ],
    'external_dependencies':
        {'python' : ['odoorpc']},
    'license': "AGPL-3",
    'data': [
        'wizards/wizard_hotel_node_reservation.xml',
        'views/node_backend_views.xml',
        'views/node_room_type_views.xml',
        'views/node_room_views.xml',
        'views/node_res_groups_views.xml',
        'views/node_res_users_views.xml',
        'views/node_res_partner_views.xml',
        'views/inherited_res_partner_views.xml',
        'views/inherited_checkpoint_views.xml',
        'security/hotel_node_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'auto_install': False,
    'installable': True
}

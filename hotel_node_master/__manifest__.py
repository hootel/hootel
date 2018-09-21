{
    'name': 'Hotel Master Node',
    'summary': """Provides centralized hotel management features""",
    'version': '0.1.0',
    'author': 'Pablo Q. Barriuso, \
               Darío Lodeiros, \
               Alexandre Díaz, \
               Odoo Community Association (OCA)',
    'category': 'Generic Modules/Hotel Management',
    'depends': [
        'project'
    ],
    'external_dependencies':
        {'python' : ['odoorpc']},
    'license': "AGPL-3",
    'data': [
        'views/hotel_node.xml',
        'views/hotel_node_user.xml',
        'views/hotel_node_group.xml',
        'views/hotel_node_room_type.xml',
        'security/hotel_node_security.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'auto_install': False,
    'installable': True
}
{
    'name': 'Hotel Master Dashboard',
    'summary': """Provides friendly and useful functions to the hotel node master module""",
    'version': '0.1.0',
    'author': 'Pablo Q. Barriuso, \
               Darío Lodeiros, \
               Alexandre Díaz, \
               Odoo Community Association (OCA)',
    'category': 'Generic Modules/Hotel Management',
    'depends': [
        'website_form',
        'hotel_node_master'
    ],
    'license': "AGPL-3",
    'data': [
        # 'security/hotel_dashboard_security.xml',
        # 'security/ir.model.access.csv'
        'views/dashboard_views.xml',
        'data/config_data.xml'
    ],
    'demo': [],
    'auto_install': False,
    'installable': True
}

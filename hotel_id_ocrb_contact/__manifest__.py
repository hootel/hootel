# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hotel Id OCR-B Contact',
    'version': '11.0.1.0',
    'author': "Alexandre Díaz <dev@redneboa.es>",
    'category': 'hotel',
    'summary': "Parse ocrb-b text image and creates a contact",
    'depends': [
        'hotel_l10n_es',
    ],
    'external_dependencies': {
        'python': ['pytesseract']
    },
    'data': [],
    'qweb': [],
    'test': [],

    'installable': True,
    'license': 'AGPL-3',
}

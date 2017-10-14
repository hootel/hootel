#-*- coding: utf-8 -*- 
from openerp import models, fields, api

class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    tourism = fields.Char('Tourism number', help='Registration number in the Ministry of Tourism. Used for INE statistics.')
    rooms = fields.Integer('Rooms Available',default=0, help='Used for INE statistics.')
    seats = fields.Integer('Beds available',default=0, help='Used for INE statistics.')
    permanentstaff = fields.Integer('Permanent Staff',default=0, help='Used for INE statistics.')
    eventualstaff = fields.Integer('Eventual Staff',default=0, help='Used for INE statistics.')
    police = fields.Char('Police number',size=10, help='Used to generate the name of the file that will be given to the police.')
    category_id = fields.Many2one('category',
            help='Hotel category in the Ministry of Tourism. Used for INE statistics.')
    cardex_warning = fields.Text('Warning in Cardex', 
        default="Hora de acceso a habitaciones: 14:00h. Hora de salida: 12:00h. Si no se abandona el alojamiento a dicha hora, el establecimiento cobrará un día de estancia según tarifa vigente ese día.",
        help="Notice under the signature on the traveler's ticket.")

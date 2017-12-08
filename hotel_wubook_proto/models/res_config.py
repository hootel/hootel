# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class WubookConfiguration(models.TransientModel):
    _name = 'wubook.config.settings'
    _inherit = 'res.config.settings'

    wubook_user = fields.Char('WuBook User')
    wubook_passwd = fields.Char('WuBook Password')
    wubook_lcode = fields.Char('WuBook lcode')
    wubook_server = fields.Char('WuBook Server', default='https://wubook.net/xrws/')
    wubook_pkey = fields.Char('WuBook PKey')


    @api.multi
    def set_wubook_user(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_user', self.wubook_user)

    @api.multi
    def set_wubook_passwd(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_passwd', self.wubook_passwd)

    @api.multi
    def set_wubook_lcode(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_lcode', self.wubook_lcode)

    @api.multi
    def set_wubook_server(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_server', self.wubook_server)

    @api.multi
    def set_wubook_pkey(self):
        return self.env['ir.values'].sudo().set_default('wubook.config.settings', 'wubook_pkey', self.wubook_pkey)

    # Dangerus method: Usefull for cloned instances with new wubook account
    @api.multi
    def resync(self):
        self.ensure_one()

        # Reset Issues
        issue_ids = self.env['wubook.issue'].search([])
        issue_ids.write({
            'to_read': False
        })

        # Push Virtual Rooms
        wubook_obj = self.env['wubook'].with_context({'init_connection': False})
        if wubook_obj.init_connection():
            ir_seq_obj = self.env['ir.sequence']
            vrooms = self.env['hotel.virtual.room'].search([])
            for vroom in vrooms:
                shortcode = ir_seq_obj.next_by_code('hotel.virtual.room')[:4]
                wrid = wubook_obj.create_room(
                    shortcode,
                    vroom.name,
                    vroom.wcapacity,
                    vroom.list_price,
                    vroom.max_real_rooms
                )
                if wrid:
                    vroom.with_context(wubook_action=False).write({
                        'wrid': wrid,
                        'wscode': shortcode,
                    })
                else:
                    vroom.with_context(wubook_action=False).write({
                        'wrid': 'none',
                        'wscode': '',
                    })
            wubook_obj.close_connection()

        # Reset Folios
        folio_ids = self.env['hotel.folio'].search([])
        folio_ids.with_context(wubook_action=False).write({
            'wseed': '',
            'whas_wubook_reservations': False,
        })

        # Reset Reservations
        reservation_ids = self.env['hotel.reservation'].search([('wrid', '!=', 'none')])
        reservation_ids.with_context(wubook_action=False).write({
            'wrid': 'none',
            'wchannel_id': False,
            'wchannel_reservation_code': 'none',
            'wis_from_channel': False,
            'wstatus': 0
        })

        # Get Parity Models
        pricelist_id = int(self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_pricelist_id'))
        restriction_id = int(self.env['ir.values'].sudo().get_default('hotel.config.settings', 'parity_restrictions_id'))

        # Put to push restrictions
        restriction_item_ids = self.env['hotel.virtual.room.restriction.item'].search([
            ('restriction_id', '=', restriction_id),
            ('applied_on', '=', '0_virtual_room'),
            ('wpushed', '=', True),
        ])
        restriction_item_ids.with_context(wubook_action=False).write({'wpushed': False})

        # Put to push pricelists
        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
            ('wpushed', '=', True),
        ])
        pricelist_item_ids.with_context(wubook_action=False).write({'wpushed': False})

        # Put to push availability
        availabity_ids = self.env['hotel.virtual.room.availabity'].search([('wpushed', '=', True)])
        availabity_ids.with_context(wubook_action=False).write({'wpushed': False})

        # Push Changes
        self.env['wubook'].push_changes()
        self.env['wubook'].push_activation()

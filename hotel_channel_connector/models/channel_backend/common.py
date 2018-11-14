# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
import binascii
from contextlib import contextmanager
from odoo import models, api, fields
from ...components.backend_adapter import WuBookLogin, WuBookServer
_logger = logging.getLogger(__name__)

class ChannelBackend(models.Model):
    _name = 'channel.backend'
    _description = 'Hotel Channel Backend'
    _inherit = 'connector.backend'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('1.2', '1.2+')]

    name = fields.Char('Name')
    version = fields.Selection(selection='select_versions', required=True)
    username = fields.Char('Channel Service Username')
    passwd = fields.Char('Channel Service Password')
    lcode = fields.Char('Channel Service lcode')
    server = fields.Char('Channel Service Server',
                         default='https://wired.wubook.net/xrws/')
    pkey = fields.Char('Channel Service PKey')
    security_token = fields.Char('Channel Service Security Token')

    reservation_id_str = fields.Char('Channel Reservation ID', store=False)

    avail_from = fields.Date('Availability From', store=False)
    avail_to = fields.Date('Availability To', store=False)

    restriction_from = fields.Date('Restriction From', store=False)
    restriction_to = fields.Date('Restriction To', store=False)
    restriction_id = fields.Many2one('channel.hotel.room.type.restriction',
                                     'Channel Restriction',
                                     store=False)

    pricelist_from = fields.Date('Pricelist From', store=False)
    pricelist_to = fields.Date('Pricelist To', store=False)
    pricelist_id = fields.Many2one('channel.product.pricelist',
                                   'Channel Product Pricelist',
                                   store=False)

    issue_ids = fields.One2many('hotel.channel.connector.issue',
                                'backend_id',
                                string='Issues')
    ota_ids = fields.One2many('channel.ota.info',
                              'backend_id',
                              string="OTA's")

    @api.multi
    def generate_key(self):
        for record in self:
            record.security_token = binascii.hexlify(os.urandom(32)).decode()

    @api.multi
    def import_reservations(self):
        channel_hotel_reservation_obj = self.env['channel.hotel.reservation']
        for backend in self:
            count = channel_hotel_reservation_obj.import_reservations(backend)
            if count == 0:
                self.env.user.notify_info("No reservations to import. All done :)",
                                          title="Import Reservations")
            else:
                self.env.user.notify_info("%d reservations successfully imported" % count,
                                          title="Import Reservations")
        return True

    @api.multi
    def import_reservation(self):
        channel_hotel_reservation_obj = self.env['channel.hotel.reservation']
        for backend in self:
            res = channel_hotel_reservation_obj.import_reservation(
                backend,
                backend.reservation_id_str)
            if res:
                self.env.user.notify_info(
                    "'%s' reservation successfully imported" % backend.reservation_id_str,
                    title="Import Reservations")
            else:
                self.env.user.notify_warning(
                    "Can't import '%s' reservation" % backend.reservation_id_str,
                    title="Import Reservations")
        return True

    @api.multi
    def import_rooms(self):
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        for backend in self:
            count = channel_hotel_room_type_obj.import_rooms(backend)
            if count == 0:
                self.env.user.notify_info("No rooms to import. All done :)",
                                          title="Import Rooms")
            else:
                self.env.user.notify_info("%d rooms successfully imported" % count,
                                          title="Import Rooms")
        return True

    @api.multi
    def import_otas_info(self):
        channel_ota_info_obj = self.env['channel.ota.info']
        for backend in self:
            count = channel_ota_info_obj.import_otas_info(backend)
            self.env.user.notify_info("%d ota's successfully imported" % count,
                                      title="Import OTA's")
        return True

    @api.multi
    def import_availability(self):
        channel_hotel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        for backend in self:
            res = channel_hotel_room_type_avail_obj.import_availability(
                backend,
                backend.avail_from,
                backend.avail_to)
            if res:
                self.env.user.notify_info("Availability successfully imported",
                                          title="Import Availability")
            else:
                self.env.user.notify_warning("Error importing availability",
                                             title="Import Availability")
        return True

    @api.multi
    def push_availability(self):
        channel_hotel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        for backend in self:
            res = channel_hotel_room_type_avail_obj.push_availability(backend)
            if res:
                self.env.user.notify_info("Availability successfully pushed",
                                          title="Export Availability")
            else:
                self.env.user.notify_warning("Error pushing availability",
                                             title="Export Availability")
        return True

    @api.multi
    def import_restriction_plans(self):
        channel_hotel_room_type_restr_obj = self.env['channel.hotel.room.type.restriction']
        for backend in self:
            count = channel_hotel_room_type_restr_obj.import_restriction_plans(backend)
            if count == 0:
                self.env.user.notify_info("No restiction plans to import. All done :)",
                                          title="Import Restrictions")
            else:
                self.env.user.notify_info("%d restriction plans successfully imported" % count,
                                          title="Import Restrictions")
        return True

    @api.multi
    def import_restriction_values(self):
        channel_hotel_restr_item_obj = self.env['channel.hotel.room.type.restriction.item']
        for backend in self:
            res = channel_hotel_restr_item_obj.import_restriction_values(
                backend,
                backend.restriction_from,
                backend.restriction_to,
                backend.restriction_id and backend.restriction_id.external_id or False)
            if res:
                self.env.user.notify_info("Restrictions successfully imported",
                                          title="Import Restrictions")
            else:
                self.env.user.notify_warning("Error importing restrictions",
                                             title="Import Restrictions")
        return True

    @api.multi
    def push_restriction(self):
        channel_hotel_restr_item_obj = self.env['channel.hotel.room.type.restriction.item']
        for backend in self:
            res = channel_hotel_restr_item_obj.push_restriction(backend)
            if res:
                self.env.user.notify_info("Restrictions successfully pushed",
                                          title="Export Restrictions")
            else:
                self.env.user.notify_warning("Error pushing restrictions",
                                             title="Export Restrictions")
        return True

    @api.multi
    def import_pricelist_plans(self):
        channel_product_pricelist_obj = self.env['channel.product.pricelist']
        for backend in self:
            count = channel_product_pricelist_obj.import_price_plans(backend)
            if count == 0:
                self.env.user.notify_info("No pricelist plans to import. All done :)",
                                          title="Import Pricelists")
            else:
                self.env.user.notify_info("%d pricelist plans successfully imported" % count,
                                          title="Import Pricelists")
        return True

    @api.multi
    def import_pricelist_values(self):
        channel_product_pricelist_item_obj = self.env['channel.product.pricelist.item']
        for backend in self:
            res = channel_product_pricelist_item_obj.import_pricelist_values(
                backend,
                backend.pricelist_from,
                backend.pricelist_to,
                backend.pricelist_id and backend.pricelist_id.external_id or False)
            if res:
                self.env.user.notify_info("Pricelists successfully imported",
                                          title="Import Pricelists")
            else:
                self.env.user.notify_warning("Error importing pricelists",
                                             title="Import Pricelists")
        return True

    @api.multi
    def push_pricelist(self):
        channel_product_pricelist_item_obj = self.env['channel.product.pricelist.item']
        for backend in self:
            res = channel_product_pricelist_item_obj.push_pricelist(backend)
            if res:
                self.env.user.notify_info("Pricelists successfully pushed",
                                          title="Export Pricelists")
            else:
                self.env.user.notify_warning("Error pushing pricelists",
                                             title="Export Pricelists")
        return True

    @api.model
    def _cron_push_changes(self):
        _logger.info("======== PASA POR AKI!!")
        backends = self.env[self._name].search([])
        for backend in backends:
            backend.push_availability()
            backend.push_restriction()
            backend.push_pricelist()

    @api.model
    def _cron_import_reservations(self):
        backends = self.env[self._name].search([])
        for backend in backends:
            backend.import_reservations()

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        wubook_login = WuBookLogin(
            self.server,
            self.username,
            self.passwd,
            self.lcode,
            self.pkey)
        with WuBookServer(wubook_login) as channel_api:
            _super = super(ChannelBackend, self)
            with _super.work_on(model_name, channel_api=channel_api, **kwargs) as work:
                yield work

    # Dangerus method: Usefull for cloned instances with new wubook account
    @api.multi
    def resync(self):
        self.ensure_one()

        now_utc_dt = fields.Date.now()
        now_utc_str = now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Reset Issues
        issue_ids = self.env['wubook.issue'].search([])
        issue_ids.write({
            'to_read': False
        })

        # Push Virtual Rooms
        wubook_obj = self.env['wubook'].with_context({
            'init_connection': False
        })
        if wubook_obj.init_connection():
            ir_seq_obj = self.env['ir.sequence']
            room_types = self.env['hotel.room.type'].search([])
            for room_type in room_types:
                shortcode = ir_seq_obj.next_by_code('hotel.room.type')[:4]
                channel_room_id = wubook_obj.create_room(
                    shortcode,
                    room_type.name,
                    room_type.wcapacity,
                    room_type.list_price,
                    room_type.total_rooms_count
                )
                if channel_room_id:
                    room_type.with_context(wubook_action=False).write({
                        'channel_room_id': channel_room_id,
                        'wscode': shortcode,
                    })
                else:
                    room_type.with_context(wubook_action=False).write({
                        'channel_room_id': '',
                        'wscode': '',
                    })
            # Create Restrictions
            room_type_rest_obj = self.env['hotel.room.type.restriction']
            restriction_ids = room_type_rest_obj.search([])
            for restriction in restriction_ids:
                if restriction.wpid != '0':
                    channel_plan_id = wubook_obj.create_rplan(restriction.name)
                    restriction.write({
                        'channel_plan_id': channel_plan_id or ''
                    })
            # Create Pricelist
            pricelist_ids = self.env['product.pricelist'].search([])
            for pricelist in pricelist_ids:
                channel_plan_id = wubook_obj.create_plan(pricelist.name, pricelist.is_daily_plan)
                pricelist.write({
                    'channel_plan_id': channel_plan_id or ''
                })
            wubook_obj.close_connection()

        # Reset Folios
        folio_ids = self.env['hotel.folio'].search([])
        folio_ids.with_context(wubook_action=False).write({
            'wseed': '',
        })

        # Reset Reservations
        reservation_ids = self.env['hotel.reservation'].search([
            ('channel_reservation_id', '!=', ''),
            ('channel_reservation_id', '!=', False)
        ])
        reservation_ids.with_context(wubook_action=False).write({
            'channel_reservation_id': '',
            'ota_id': False,
            'ota_reservation_id': '',
            'is_from_ota': False,
            'wstatus': 0
        })

        # Get Default Models
        pricelist_id = int(self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id'))
        restriction_id = int(self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_restriction_id'))

        room_type_restr_it_obj = self.env['hotel.room.type.restriction.item']
        # Secure Wubook Input
        restriction_item_ids = room_type_restr_it_obj.search([
            ('applied_on', '=', '0_room_type'),
            ('date_start', '<', now_utc_str),
        ])
        if any(restriction_item_ids):
            restriction_item_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push restrictions
        restriction_item_ids = room_type_restr_it_obj.search([
            ('restriction_id', '=', restriction_id),
            ('applied_on', '=', '0_room_type'),
            ('wpushed', '=', True),
            ('date_start', '>=', now_utc_str),
        ])
        if any(restriction_item_ids):
            restriction_item_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Secure Wubook Input
        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
            ('date_start', '<', now_utc_str),
        ])
        if any(pricelist_item_ids):
            pricelist_item_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push pricelists
        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
            ('wpushed', '=', True),
            ('date_start', '>=', now_utc_str),
        ])
        if any(pricelist_item_ids):
            pricelist_item_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Secure Wubook Input
        availabity_ids = self.env['hotel.room.type.availability'].search([
            ('date', '<', now_utc_str),
        ])
        if any(availabity_ids):
            availabity_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push availability
        availabity_ids = self.env['hotel.room.type.availability'].search([
            ('wpushed', '=', True),
            ('date', '>=', now_utc_str),
        ])
        if any(availabity_ids):
            availabity_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Generate Security Token
        self.env['ir.default'].sudo().set(
            'wubook.config.settings',
            'wubook_push_security_token',
            binascii.hexlify(os.urandom(16)).decode())
        self.env.cr.commit()    # FIXME: Need do this

        # Push Changes
        if wubook_obj.init_connection():
            wubook_obj.push_activation()
            wubook_obj.import_channels_info()
            wubook_obj.push_changes()
            wubook_obj.close_connection()

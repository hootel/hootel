# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeRestrictionImporter(Component):
    _name = 'channel.hotel.room.type.restriction.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.importer'

    @api.model
    def import_restriction_plans(self):
        results = self.backend_adapter.rplan_rplans()
        channel_restriction_obj = self.env['channel.hotel.room.type.restriction']
        restriction_mapper = self.component(usage='import.mapper',
                                            model_name='channel.hotel.room.type.restriction')
        for plan in results:
            plan_record = restriction_mapper.map_record(plan)
            plan_bind = channel_restriction_obj.search([
                ('external_id', '=', str(plan['id']))
            ], limit=1)
            if not plan_bind:
                channel_restriction_obj.with_context({
                    'connector_no_export': True,
                    'rules': plan.get('rules'),
                }).create(plan_record.values(for_create=True))
            else:
                plan_bind.with_context({'connector_no_export':True}).write(
                    plan_record.values())
            count = count + 1
        return count


class HotelRoomTypeRestrictionImportMapper(Component):
    _name = 'channel.hotel.room.type.restriction.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type.restriction'

    direct = [
        ('name', 'name'),
        ('id', 'external_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoorpc
import logging
from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
_logger = logging.getLogger(__name__)


class NodeLogin(object):
    def __init__(self, address, protocol, port, db, user, passwd):
        self.address = address
        self.protocol = protocol
        self.port = port
        self.db = db
        self.user = user
        self.passwd = passwd


class NodeServer(object):
    def __init__(self, login_data):
        self._server = None
        self._login_data = login_data

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, type, value, traceback):
        if self._server is not None:
            self.close()

    @property
    def server(self):
        if self._server is None:
            try:
                self._server = odoorpc.ODOO(self._login_data.address,
                                            self._login_data.protocol,
                                            self._login_data.port)
                self._server.login(self._login_data.db,
                                   self._login_data.user,
                                   self._login_data.passwd)
            except Exception:
                self._server = None
                raise RetryableJobError("Can't connect with node!")
        return self._server

    def close(self):
        self._server.logout()
        self._server = None


class HotelNodeInterfaceAdapter(AbstractComponent):
    _name = 'hotel.node.interface.adapter'
    _inherit = ['base.backend.adapter', 'base.node.connector']
    _usage = 'backend.adapter'

    # === ROOM TYPES
    def create_room_type(self, name, room_ids):
        raise NotImplementedError

    def modify_room_type(self, room_type_id, name, room_ids):
        raise NotImplementedError

    def delete_room_type(self, room_type_id):
        raise NotImplementedError

    def fetch_room_types(self):
        raise NotImplementedError

    # === ROOMS
    def create_room(self, name, capacity, room_type_id):
        raise NotImplementedError

    def modify_room(self, room_id, name, capacity, room_type_id):
        raise NotImplementedError

    def delete_room(self, room_id):
        raise NotImplementedError

    def fetch_rooms(self):
        raise NotImplementedError

    @property
    def _server(self):
        try:
            node_server = getattr(self.work, 'node_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a node_api attribute with a '
                'WuBookServer instance to be able to use the '
                'Backend Adapter.'
            )
        return node_server.server


class HotelNodeAdapter(AbstractComponent):
    _name = 'hotel.node.adapter'
    _inherit = 'hotel.node.interface.adapter'

    # === ROOM TYPES
    def create_room_type(self, name, room_ids):
        return self._server.env['hotel.room.type'].create({
            'name': name
        })

    def modify_room_type(self, room_type_id, name, rooms_id):
        return self._server.env['hotel.room.type'].write(
            [room_type_id],
            {
                'name': name
            })

    def delete_room_type(self, room_type_id):
        _logger.warning("_delete_room_type(%s, room_type_id) is not yet implemented.", self)
        return True
        # return self._server.env['hotel.room.type'].unlink(room_type_id)

    def fetch_room_types(self):
        return self._server.env['hotel.room.type'].search_read(
            [],
            ['name', 'room_ids']
        )

    # === ROOMS
    def create_room(self, name, capacity, room_type_id):
        return self._server.env['hotel.room'].create({
            'name': name,
            'capacity': capacity,
            'room_type_id': room_type_id,
        })

    def modify_room(self, room_id, name, capacity, room_type_id):
        return self._server.env['hotel.room'].write(
            [room_id],
            {
                'name': name,
                'capacity': capacity,
                'room_type_id': room_type_id,
            })

    def delete_room(self, room_id):
        return self._server.env['hotel.room'].unlink(room_id)

    def fetch_rooms(self):
        rooms = self._server.env['hotel.room'].search_read(
            [],
            ['name', 'capacity', 'room_type_id']
        )
        for rec in rooms:
            rec['room_type_id'] = rec['room_type_id'][0]

        return rooms


    # === PARTNERS
    def create_res_partner(self, name, email, is_company, type):
        return self._server.env['node.res.partner'].create({
            'name': name,
            'email': email,
            'is_company': is_company,
            'type': type,
        })

    def modify_res_partner(self, partner_id, name, email, is_company, type):
        return self._server.env['node.res.partner'].write(
            [partner_id],
            {
                'name': name,
                'email': email,
                'is_company': is_company,
                'type': type,
            })

    def delete_res_partner(self, partner_id):
        _logger.warning("_delete_partner(%s, room_type_id) is not yet implemented.", self)
        # return self._server.env['node.res.partner'].unlink(partner_id)

    def fetch_res_partners(self):
        rooms = self._server.env['node.res.partner'].search_read(
            [],
            ['name', 'email', 'is_company', 'type']
        )
        return rooms

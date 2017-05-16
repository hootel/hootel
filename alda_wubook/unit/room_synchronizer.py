from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Exporter
from ..bakend import wubook
from .room_adapter import WuBookCRUDAdapter
import xmlrpclib
import logging
_logger = logging.getLogger(__name__)


@wubook
class RoomAdapter(WuBookCRUDAdapter):
    _model_name = 'wubook.hotel.virtual.room'

    def create(self, room, wserver, user, passwd, lcode, pkey):
        """ Create a room. """


        _logger.info("PASA 11")

        wServer = xmlrpclib.Server(wserver)
        res, tok = wServer.acquire_token(user, passwd, pkey)

        _logger.info("PASA 22")

        shortcode = "V%d" % room.id
        res, rid = wServer.new_room(
            tok,
            lcode,
            0,
            room.name,
            room.total_rooms_count,
            room.price,
            1,
            shortcode[:4],
            'nb',
            rtype=room.shared and 3 or 1
        )

        wServer.release_token(tok)

        room.virtual_code = rid

        _logger.info("PASA FIN")

        return True


@wubook
class RoomSynchronizer(Exporter):
    _model_name = ['wubook.hotel.virtual.room']

    def _export_room(self, room):
        # use the ``backend adapter`` to create the invoice
        return self.backend_adapter.create(room)

    def run(self, binding_id, wserver, user, passwd, lcode, pkey):
        """ Run the job to export the validated/paid invoice """
        room = self.model.browse(binding_id)
        wubook_id = self._export_room(room, wserver, user, passwd, lcode, pkey)
        # use the ``binder`` to write the external ID
        self.binder.bind(wubook_id, binding_id)

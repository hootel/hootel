# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import xml.etree.cElementTree as ET


class Inherited_hotel_folio(models.Model):

    _inherit = 'hotel.folio'


@api.model
def RmGetReservation(self, Code=False):
    xml_response = ET.Element("GetReservationResult")
    return xml_response

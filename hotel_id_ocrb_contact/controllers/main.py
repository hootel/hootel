# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
import io
from PIL import Image
from odoo import http
from tools.image2text import Bitmap2Text
_logger = logging.getLogger(__name__)


class HotelOCRBContact(http.Controller):
    @http.route(['/hotel/ocrb'], type='json', cors="*", auth="none")
    def hotel_ocrb_contact(self, image64):

        imgdata = base64.b64decode(str(image64))
        image = Image.open(io.BytesIO(imgdata))

        result = Bitmap2Text().run(image)

        _logger.info(result)

        return True

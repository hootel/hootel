# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import pytesseract
from odoo import http


class HotelOCRBContact(http.Controller):
    @http.route(['/hotel/ocrb'], type='json', cors="*", auth="none")
    def hotel_ocrb_contact(self, image):

        image_bin = base64.decodestring(image)
        text = pytesseract.image_to_string(image_bin)
        print(text)

        return True

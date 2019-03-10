# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
from odoo import http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from ..tools.image2text import Image2Text
_logger = logging.getLogger(__name__)


class HotelOCRBContact(http.Controller):
    @http.route(['/hotel/ocrb'], type='json', cors="*", auth="none",
                website=True)
    def hotel_ocrb_contact(self, image64):

        imgdata = base64.b64decode(str(image64))
        image = Image.open(io.BytesIO(imgdata))
        result = Image2Text().run(image)

        dnieExpeditionDate = self._getExpeditionDate(
            result['birthday'], result['endDate'])
        osex = "other"
        if 'M' == result['sex']:
            osex = "male"
        elif 'F' == result['sex']:
            osex = "female"

        request.env['res.partner'].sudo().create({
            'name': result['name'],
            'document_number': result['dni'],
            'birthdate_date': result['birthday'].strftime(
                DEFAULT_SERVER_DATETIME_FORMAT),
            'gender': osex,
            'document_expedition_date': dnieExpeditionDate
            and dnieExpeditionDate.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'comment': "Nation: %s" % result['nation'],
        })

        return True

    def _getExpeditionDate(self, birthday, expiry):
        def calculate_age(born, begin=None):
            if not begin:
                begin = datetime.now()
            return begin.year - born.year \
                - ((begin.month, begin.day) < (born.month, born.day))

        age = calculate_age(birthday)
        diff = calculate_age(datetime.now(), expiry)
        result = expiry
        if age < 5:
            if diff > 2:
                result -= relativedelta(years=2)
        elif age >= 5 and age < 30:
            if diff <= 5:
                result -= relativedelta(years=2)
            else:
                result -= relativedelta(years=5)
        elif age >= 30 and age < 70:
            if diff <= 5:
                result -= relativedelta(years=5)
            else:
                result -= relativedelta(years=10)
        else:
            return None
        return result

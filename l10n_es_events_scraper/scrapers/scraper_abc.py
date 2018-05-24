# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
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
from datetime import datetime, timedelta
from time import sleep
import requests
import re
try:
    from urllib.parse import quote_plus
except ImportError:     # Python 2
    from urllib import quote_plus
import logging
_logger = logging.getLogger(__name__)


REQUEST_DELAY = 3
MONTHS_MAP = {
    'Enero': 1,
    'Febrero': 2,
    'Marzo': 3,
    'Abril': 4,
    'Mayo': 5,
    'Junio': 6,
    'Julio': 7,
    'Agosto': 8,
    'Septiembre': 9,
    'Octubre': 10,
    'Noviembre': 11,
    'Diciembre': 12,
}


class EventCity:
    def __init__(self, postid=0, city='', dates=None, name='', address='',
                 venue='', prices='', buy_tickets=''):
        self.postid = postid
        self.city = city
        self.dates = dates or []
        self.name = name
        self.address = address
        self.venue = venue
        self.prices = prices
        self.buy_tickets = buy_tickets


def analize_page(url, onlyFuture):
    r = requests.get(url)
    if r.status_code == 200:
        now = datetime.now()
        eventCity = EventCity()
        # Post ID
        res = re.search(r'postid-(\d+)', r.text)
        if res:
            eventCity.postid = res.group(1)
        # Name
        res = re.search(
            r'<h1 class="entry-title"><a href="[^"]+" rel="bookmark" title="(?:Entradas\s)?([^"]+)">',
            r.text, re.I)
        if res:
            eventCity.name = res.group(1)
        # Date
        res = re.search(r'<p><strong>Fecha:<\/strong>\s(.*?)<\/p>',
                        r.text,
                        re.I)
        if not res:
            res = re.search(
                r'<p><strong>Fecha\sy\shora:<\/strong>\s(.*?)<\/p>',
                r.text,
                re.I)
        if res:
            res = re.search(
                r'\w+\s(\d+)\sde\s(\w+)\sde\s(\d+)\sa\slas\s(\d+):(\d+)\shoras',
                res.group(1),
                re.U | re.I)
            if res:
                cdate = datetime(
                    int(res.group(3)),
                    MONTHS_MAP[res.group(2)],
                    int(res.group(1)),
                    int(res.group(4)),
                    int(res.group(5)),
                    0)
                if not onlyFuture or cdate >= now:
                    eventCity.dates.append(cdate)
        else:
            res = re.search(
                ur'<p><strong>Fechas\sy\días:<\/strong>\s(.*?)<\/p>',
                r.text,
                re.I)
            if res:
                res = re.search(
                    r'Del\s(\d+)\sal\s(\d+)\sde\s(\w+)\sde\s(\d+)',
                    res.group(1),
                    re.U | re.I)
                if res:
                    date_begin = datetime(
                        int(res.group(4)),
                        MONTHS_MAP[res.group(3)],
                        int(res.group(1)),
                        0,
                        0,
                        0)
                    date_end = datetime(
                        int(res.group(4)),
                        MONTHS_MAP[res.group(3)],
                        int(res.group(2)),
                        0,
                        0,
                        0)
                    diff = abs((date_end - date_begin).days)
                    for i in range(diff):
                        cdate = date_begin + timedelta(days=i)
                        if not onlyFuture or cdate >= now:
                            eventCity.dates.append(cdate)
        # Avenue
        res = re.search(r'<p><strong>Lugar:<\/strong>\s(.*?)<\/p>',
                        r.text,
                        re.I)
        if res:
            eventCity.venue = res.group(1)
        # Address
        res = re.search(ur'<p><strong>Dirección:<\/strong>\s(.*?)<\/p>',
                        r.text,
                        re.I)
        if res:
            eventCity.address = res.group(1)
        # Buy Tickets
        res = re.search(
            r'<p><strong>Venta de entradas:<\/strong>\s(.*?)<\/p>',
            r.text,
            re.I)
        if res:
            eventCity.buy_tickets = res.group(1)
        # Prices
        res = re.search(r'<p><strong>Precios:<\/strong>\s(.*?)<\/p>',
                        r.text,
                        re.I)
        if res:
            eventCity.prices = res.group(1)

        if not any(eventCity.dates):
            return False

        return eventCity
    else:
        return False


def import_city_events(events, search, npag=1, pags=-1,
                       onlyFuture=False):
    pags = pags if pags == -1 else (pags-1)
    E_URL = 'http://www.entradasyconciertos.com'
    frmt_page = u'/page/%d/?s=%s' % (npag, quote_plus(search))
    r = requests.get('%s%s' % (E_URL, frmt_page))
    if r.status_code == 200:
        # Get Pagination
        pages = re.search(
            ur"<span class='pages'>Página (\d+) de (\d+)</span>",
            r.text)
        total_pags = int(pages.group(2))

        res_founds = re.finditer(
            r'<h2 class="entry-title"><a href="([^"]+)" rel="bookmark">',
            r.text)
        for res in res_founds:
            sleep(REQUEST_DELAY)
            nevent = analize_page(res.group(1), onlyFuture)
            if nevent:
                events.append(nevent)

        # Recursive Call
        if npag < total_pags and pags != 0:
            sleep(REQUEST_DELAY)
            import_city_events(events,
                               search,
                               npag=npag+1,
                               pags=pags,
                               onlyFuture=onlyFuture)
    else:
        raise Exception("Unespected Error!")

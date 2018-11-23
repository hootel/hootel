# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HotelDashboard(http.Controller):

    @http.route('/hotel/dashboard/',
                auth='public', website=True)
    def index(self, **kw):
        backends = request.env['node.backend'].search([])
        return http.request.render('hotel_dashboard_master.dashboard_page', {'backends': backends})

    @http.route('/hotel/dashboard/<model("node.backend"):backend>',
                auth='public', website=True)
    def backend(self, backend, **kw):
        values = {
            'backend': backend,
        }
        return http.request.render('hotel_dashboard_master.dashboard_backend_view', values)


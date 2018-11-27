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
    def show_backend(self, backend, **kw):
        # show a summary of the hotel, room types and relevant information
        values = {
            'backend': backend,
            'room_types': request.env['node.room.type'].search([
                ('backend_id', '=', backend.id),
            ]),
            'header_tab': 'backend',
        }
        return http.request.render('hotel_dashboard_master.dashboard_backend_view', values)

    @http.route([
        '/hotel/dashboard/<model("node.backend"):backend>/room_types/',
        '/hotel/dashboard/<model("node.backend"):backend>/room_types/<model("node.room.type"):room_type>',
        '/hotel/dashboard/<model("node.backend"):backend>/room_types/<model("node.room.type"):room_type>/rooms/<model("node.room"):room>'
        ], auth='public', website=True)
    def show_backend_room_types(self, backend, room_type=None, **kw):
        values = {
            'backend': backend,
            'header_tab': 'room_types',
        }
        if room_type:
            values['rooms'] = request.env['node.room'].search([
                ('backend_id', '=', backend.id),
                ('room_type_id', '=', room_type.id),
            ])
            values['room_type'] = room_type
        else:
            values['room_types'] = request.env['node.room.type'].search([
                ('backend_id', '=', backend.id),
            ])

        return http.request.render('hotel_dashboard_master.dashboard_room_types_view', values)

    @http.route('/hotel/dashboard/<model("node.backend"):backend>/wizard_reservation/',
             auth='public', website=True)
    def show_wizard_reservation_(self, backend, **kw):
        values = {
            'backend': backend,
            'header_tab': 'wizard_reservation',
            'partners' : request.env['res.partner'].search([]),
        }
        return http.request.render('hotel_dashboard_master.dashboard_wizard_reservation', values)

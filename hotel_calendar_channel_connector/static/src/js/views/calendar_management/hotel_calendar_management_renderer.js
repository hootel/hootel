/* global $, odoo, _, HotelCalendar, moment */
// Copyright 2019 Alexandre Díaz <dev@redneboa.es>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
odoo.define('hotel_calendar_channel_connector.MPMSCalendarRenderer', function (require) {
"use strict";

var MPMSCalendarRenderer = require('hotel_calendar.MPMSCalendarRenderer');

var HotelCalendarManagementRendererChannelConnector = MPMSCalendarRenderer.include({
    /** CUSTOM METHODS **/
    get_values_to_save: function() {
        var oparams = this._super.apply(this, arguments);
        var availability = this._hcalendar.getAvailability(true);
        oparams.push(availability);

        return oparams;
    },
});

return HotelCalendarManagementRendererChannelConnector;

});

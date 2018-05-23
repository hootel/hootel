odoo.define('hotel_calendar.listview_button_open_reservation_wizard', function(require) {
'use strict';
/*
 * Hotel WuBook
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 */

var ListView = require('web.ListView');
var Core = require('web.core');

var _t = Core._t;


ListView.include({
	render_buttons: function () {
		var self = this;
		this._super.apply(this, arguments); // Sets this.$buttons

		if (this.dataset.model == 'hotel.reservation') {
			this.$buttons.append("<button class='oe_button oe_open_reservation_wizard oe_highlight' type='button'>"+_t('Open Wizard')+"</button>");
			this.$buttons.find('.oe_open_reservation_wizard').on('click', function(){
				self.do_action('hotel_calendar.open_wizard_reservations');
			});
		}
  }
});

});

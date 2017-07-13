odoo.define('wubook.listview_button_import_rooms', function(require) {
'use strict';
/*
 * Hotel WuBook
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */

var ListView = require('web.ListView');
var Core = require('web.core');

var _t = Core._t;

function import_rooms(){
	var self = this;
    this.dataset._model.call('import_rooms', [false]).then(function(results){
			if (!results[0]) {
				self.do_warn(_t('Operation Errors'), _t('Errors while importing rooms. See issues registry.'), true);
			}
			if (results[0] || results[1] > 0) {
				if (results[1] > 0) {
					self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Rooms successfully imported'), false);
				} else {
					self.do_notify(_t('Operation Success'), _t('No new rooms found. All are done.'), false);
				}
        var active_view = self.ViewManager.active_view;
        active_view.controller.reload(); // list view only has reload
			}
	});

	return false;
}

function import_reservations(){
	var self = this;
	this.dataset._model.call('import_reservations', [false]).then(function(results){
		console.log(results);
		if (!results[0]) {
			self.do_warn(_t('Operation Errors'), _t('Errors while importing reservations. See issues registry.'), true);
		}
		if (results[0] || results[1] > 0) {
			if (results[1] > 0) {
				self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Reservations successfully imported'), false);
			} else {
				self.do_notify(_t('Operation Success'), _t('No new reservations found. All are done.'), false);
			}
			var active_view = self.ViewManager.active_view;
      active_view.controller.reload(); // list view only has reload
		}
	});

	return false;
}

function import_price_plans(){
	var self = this;
	this.dataset._model.call('import_price_plans', [false]).then(function(results){
		if (!results[0]) {
			self.do_warn(_t('Operation Errors'), _t('Errors while importing price plans from WuBook. See issues log.'), true);
		}
		if (results[0] || results[1] > 0) {
			if (results[1] > 0) {
				self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Price Plans successfully imported'), false);
			} else {
				self.do_notify(_t('Operation Success'), _t('No new price plans found. All are done.'), false);
			}
      var active_view = self.ViewManager.active_view;
      active_view.controller.reload(); // list view only has reload
		}
	});

	return false;
}

function import_channels_info(){
	var self = this;
	this.dataset._model.call('import_channels_info', [false]).then(function(results){
		if (!results[0]) {
			self.do_warn(_t('Operation Errors'), _t('Errors while importing channels info from WuBook. See issues log.'), true);
		}
		if (results[0] || results[1] > 0) {
			if (results[1] > 0) {
				self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Channels Info successfully imported'), false);
			} else {
				self.do_notify(_t('Operation Success'), _t('No new channels info found. All are done.'), false);
			}
      var active_view = self.ViewManager.active_view;
      active_view.controller.reload(); // list view only has reload
		}
	});

	return false;
}

function import_restriction_plans(){
	var self = this;
	this.dataset._model.call('import_restriction_plans', [false]).then(function(results){
		if (!results[0]) {
			self.do_warn(_t('Operation Errors'), _t('Errors while importing restriction plans from WuBook. See issues log.'), true);
		}
		if (results[0] || results[1] > 0) {
			if (results[1] > 0) {
				self.do_notify(_t('Operation Success'), `<b>${results[1]}</b>` + ' ' + _t('Restriction Plans successfully imported'), false);
			} else {
				self.do_notify(_t('Operation Success'), _t('No new restriction plans found. All are done.'), false);
			}
      var active_view = self.ViewManager.active_view;
      active_view.controller.reload(); // list view only has reload
		}
	});

	return false;
}

function import_availability(){
  this.do_action('hotel_wubook_proto.action_wubook_import_availability');
	return false;
}

ListView.include({
	render_buttons: function() {
		this._super.apply(this, arguments); // Sets this.$buttons

		if (this.dataset.model == 'hotel.virtual.room') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_rooms oe_highlight' type='button'>Import Rooms From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_rooms').on('click', import_rooms.bind(this));
        } else if (this.dataset.model == 'hotel.folio') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_reservations oe_highlight' type='button'>Import Reservations From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_reservations').on('click', import_reservations.bind(this));
        } else if (this.dataset.model == 'product.pricelist') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_price_plans oe_highlight' type='button'>Import Price Plans From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_price_plans').on('click', import_price_plans.bind(this));
        } else if (this.dataset.model == 'wubook.channel.info') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_channels_info oe_highlight' type='button'>Import Channels Info From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_channels_info').on('click', import_channels_info.bind(this));
        } else if (this.dataset.model == 'reservation.restriction') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_restriction_plans oe_highlight' type='button'>Import Restriction Plans From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_restriction_plans').on('click', import_restriction_plans.bind(this));
        } else if (this.dataset.model == 'virtual.room.availability') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_availability oe_highlight' type='button'>Import Availability From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_availability').on('click', import_availability.bind(this));
        }
    }
});

});

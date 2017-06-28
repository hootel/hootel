odoo.define('wubook.listview_button_import_rooms', function(require) {
'use strict';
/*
 * Hotel WuBook
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */

var ListView = require('web.ListView');

function import_rooms(){
	var self = this;
    this.dataset._model.call('import_rooms', [false]).then(function(results){
        var active_view = self.ViewManager.active_view;
        active_view.controller.reload(); // list view only has reload
	});
 
	return false;
}
    
function import_reservations(){
	var self = this;
	this.dataset._model.call('import_reservations', [false]).then(function(results){
        var active_view = self.ViewManager.active_view;
        active_view.controller.reload(); // list view only has reload
	});
 
	return false;
}

function import_price_plans(){
	var self = this;
	this.dataset._model.call('import_price_plans', [false]).then(function(results){
        var active_view = self.ViewManager.active_view;
        active_view.controller.reload(); // list view only has reload
	});
 
	return false;
}

function import_channels_info(){
	var self = this;
	this.dataset._model.call('import_channels_info', [false]).then(function(results){
        var active_view = self.ViewManager.active_view;
        active_view.controller.reload(); // list view only has reload
	});
 
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
        }
    }
});

});

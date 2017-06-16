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
    
ListView.include({
	render_buttons: function() {
		this._super.apply(this, arguments); // Sets this.$buttons
        
		if (this.dataset.model == 'hotel.virtual.room') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_rooms oe_highlight' type='button'>Import Rooms From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_rooms').on('click', import_rooms.bind(this));
        } else if (this.dataset.model == 'hotel.folio') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_reservations oe_highlight' type='button'>Import Reservations From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_reservations').on('click', import_reservations.bind(this));
        }
    }
});

});

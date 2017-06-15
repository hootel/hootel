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
	var $this = this;
    this.dataset._model.call('import_rooms', [false]).then(function(results){
    	if ($this.action_manager.inner_widget && typeof $this.action_manager.inner_widget !== 'undefined')
    	{
            var active_view = $this.action_manager.inner_widget.active_view;
            if (typeof active_view !== 'undefined')
            {
            	var controller = this.action_manager.inner_widget.views[active_view].controller;
		    	if (active_view == "kanban")
		            controller.do_reload(); // kanban view has do_reload
		        else
		            controller.reload(); // list view only has reload
            }
    	}
	});
 
	return false;
}
    
function import_reservations(){
	var $this = this;
	this.dataset._model.call('import_reservations', [false]).then(function(results){
    	if ($this.action_manager.inner_widget && typeof $this.action_manager.inner_widget !== 'undefined')
    	{
            var active_view = $this.action_manager.inner_widget.active_view;
            if (typeof active_view !== 'undefined')
            {
            	var controller = this.action_manager.inner_widget.views[active_view].controller;
		    	if (active_view == "kanban")
		            controller.do_reload(); // kanban view has do_reload
		        else
		            controller.reload(); // list view only has reload
            }
    	}
	});
 
	return false;
}
    
ListView.include({
	render_buttons: function() {
		this._super.apply(this, arguments); // Sets this.$buttons
        
		if (this.dataset.model == 'hotel.virtual.room') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_rooms oe_highlight' type='button'>Import Rooms From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_rooms').on('click', import_rooms.bind(this));
        }
        else if (this.dataset.model == 'hotel.folio') {
        	this.$buttons.append("<button class='oe_button oe_wubook_import_reservations oe_highlight' type='button'>Import Reservations From WuBook</button>");
        	this.$buttons.find('.oe_wubook_import_reservations').on('click', import_reservations.bind(this));
        }
    }
});

});

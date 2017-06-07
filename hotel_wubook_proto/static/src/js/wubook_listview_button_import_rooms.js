odoo.define('wubook.listview_button_import_rooms', function(require) {
    'use strict';
    
    var ListView = require('web.ListView');
    
    function import_rooms(){ 
        this.dataset._model.call('import_rooms', [false]).then(function(results){
        	window.location.reload();
        });
 
        return false;
    }
    
    function import_reservations(){
        this.dataset._model.call('import_reservations', [false]).then(function(results){
        	window.location.reload();
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

odoo.define('wubook.listview_button_import_rooms', function(require) {
    'use strict';
    
    var ListView = require('web.ListView');
    
    function import_rooms(){
        var self = this;
        
        console.log(this.dataset._model);
        
        this.dataset._model.call('import_rooms', [false]).then(function(results){
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
        }
    });
});

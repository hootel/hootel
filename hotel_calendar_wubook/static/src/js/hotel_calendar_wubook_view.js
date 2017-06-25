odoo.define('hotel_calendar_wubook.HotelCalendarViewWuBook', function(require) {
'use strict';
/*
 * Hotel Calendar WuBook View
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */

var HotelCalendarView = require('hotel_calendar.HotelCalendarView');
var Model = require('web.DataModel');
var Common = require('web.form_common');
var Core = require('web.core');
var Session = require('web.session');

var _t = Core._t;
var _wubook_notif_reservations_domain = [
	['wrid', '!=', 'none'],
	'|', ['to_assign', '=', true], ['to_read', '=', true]
];

var HotelCalendarViewWuBook = HotelCalendarView.include({
	update_buttons_counter: function() {
		this._super();
		var self = this;
		
		// Cloud Reservations
    	new Model('hotel.reservation').call('search_count', [_wubook_notif_reservations_domain]).then(function(count){
    		var $button = self.$el.find("#btn_channel_manager_request");
    		var $text = self.$el.find("#btn_channel_manager_request .cloud-text");
			if (count > 0) {
				$button.addClass('incoming');
				$text.text(count);
				$text.show();
			} else {
				$button.removeClass('incoming');
				$text.hide();
			}
		});
	},
	
	init_calendar_view: function() {
		var self = this;
		return $.when(this._super()).then(function(){
            var deferred_promises = [];
			self.$el.find("#btn_channel_manager_request").on('click', function(ev){
				var pop = new Common.SelectCreateDialog(self, {
	                res_model: 'hotel.reservation',
	                domain: _wubook_notif_reservations_domain,
	                title: _t("WuBook Reservations to Assign"),
	                disable_multiple_selection: true,
	                no_create: true,
	                on_selected: function(element_ids) {
	                	return self._model.call('get_formview_id', [element_ids[0], Session.user_context]).then(function(view_id){
	        				var popView = new Common.FormViewDialog(self, {
	        	                res_model: 'hotel.reservation',
	        	                res_id: element_ids[0],
	        	                title: _t("Open: ") + _t("Reservation"),
	        	                view_id: view_id
	        	            }).open();
	        				popView.on('write_completed', self, function(){
	                            self.trigger('changed_value');
	                        });
	        				popView.on('closed', self, function(){
	                            self.reload_hcalendar_reservations(); // Here because don't trigger 'write_completed' when change state to confirm
	                        });
	        			});
	                }
	            }).open();
			});
			
			return $.when.apply($, deferred_promises);
		});
	}
});

return HotelCalendarViewWuBook;

});

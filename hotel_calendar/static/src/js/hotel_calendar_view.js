odoo.define('hotel_calendar.HotelCalendarView', function (require) {
"use strict";
/*
 * Hotel Calendar View
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */
/* TODO (TOFIX):
 *  1. Performance... calendar redraw 2 times and reservations 4 times when change dates!!
 *        - 2 times for movement calendar (redraw all!) [1 Checkin data change, 1 Checkout data change]
 *        - 2 times for new reservations (post-move) [1 Checkin data change, 1 Checkout data change]
 *        Can reduce easy to 2 times for all if adds 'search' button instead use 'onchange' events.
 */

var Core = require('web.core');
var Bus = require('bus.bus').bus;
//var data = require('web.data');
var Time = require('web.time');
var Model = require('web.DataModel');
var View = require('web.View');
var Common = require('web.form_common');
//var pyeval = require('web.pyeval');
var ActionManager = require('web.ActionManager');
var Utils = require('web.utils');
var Dialog = require('web.Dialog');
var Ajax = require('web.ajax');
var ControlPanel = require('web.ControlPanel');
var Session = require('web.session');

var _t = Core._t;
var _lt = Core._lt;
var QWeb = Core.qweb;
var l10n = _t.database.parameters;

var PUBLIC_PRICELIST_ID = 1; // Hard-Coded public pricelist id
var ODOO_DATETIME_MOMENT_FORMAT = "YYYY-MM-DD HH:mm:ss";
var L10N_DATETIME_MOMENT_FORMAT = Time.strftime_to_moment_format(l10n.date_format + ' ' + l10n.time_format);
var L10N_DATE_MOMENT_FORMAT = Time.strftime_to_moment_format(l10n.date_format);


/* HIDE CONTROL PANEL */
/* FIXME: Look's like a hackish solution */
ControlPanel.include({
    update: function(status, options) {
    	this._super(status, options);
    	var action_stack = this.getParent().action_stack;
    	if (action_stack && action_stack.length) {
    		var active_action = action_stack[action_stack.length-1];
	    	if (active_action.widget && active_action.widget.active_view &&
	    			active_action.widget.active_view.type === 'pms'){
	            this._toggle_visibility(false);
	        } else {
	        	this._toggle_visibility(true);
	        }
    	}
    }
});

var HotelCalendarView = View.extend({
	/** VIEW OPTIONS **/
	template: "hotel_calendar.HotelCalendarView",
    display_name: _lt('Hotel Calendar'),
    icon: 'fa fa-map-marker',
    view_type: "pms",
    searchable: false,
    searchview_hidden: true,
    
    // Custom Options
    _model: null,
    _hcalendar: null,
    _reserv_tooltips: {},
    _action_manager: null,
    _flag_ignore_action: false,
    
    /** VIEW METHODS **/
    init: function(parent, dataset, view_id, options) {
        this._super(parent);
        this.ready = $.Deferred();
        this.set_default_options(options);
        this.dataset = dataset;
        this.model = dataset.model;
        this.fields_view = {};
        this.view_id = view_id;
        this.view_type = 'pms';
        this.selected_filters = [];
        this.mutex = new Utils.Mutex();
        this._model = new Model(this.dataset.model);
        this._action_manager = this.findAncestor(function(ancestor){ return ancestor instanceof ActionManager; });
        
        Bus.on("notification", this, this._on_bus_signal);
    },    

    view_loading: function(r) {
        return this.load_custom_view(r);
    },

    load_custom_view: function(fv) {
    	/* xml view calendar options */
        var attrs = fv.arch.attrs,
            self = this;
        this.fields_view = fv;

        var edit_check = new Model(this.dataset.model)
        	.call("check_access_rights", ["write", false])
        	.then(function (write_right) {
        		self.write_right = write_right;
        	});
	    var init = new Model(this.dataset.model)
	        .call("check_access_rights", ["create", false])
	        .then(function (create_right) {
	            self.create_right = create_right;
	            self.init_calendar_view().then(function() {
	                //$(window).trigger('resize');
	                self.trigger('hotel_calendar_view_loaded', fv);
	                self.ready.resolve();
	            });
	        });
	    return $.when(edit_check, init);
    },
    
    do_show: function() {
    	var $widget = this.$el.find("#hcal_widget");
        if ($widget) {
        	$widget.show();
        }
        this.do_push_state({});
        return this._super();
    },
    do_hide: function () {
    	var $widget = this.$el.find("#hcal_widget");
        if ($widget) {
        	$widget.hide();
        }
        return this._super();
    },
    is_action_enabled: function(action) {
        if (action === 'create' && !this.options.creatable) {
            return false;
        }
        return this._super(action);
    },
    
    destroy: function () {
        return this._super.apply(this, arguments);
    },
    
    /** CUSTOM METHODS **/
    create_calendar: function(options, pricelist) {
    	var self = this;
    	// CALENDAR
    	if (this._hcalendar) {
    		delete this._hcalendar;
    	}
		var $widget = this.$el.find("#hcal_widget");
		var $hcal = $widget.find('#hcalendar');
		if ($hcal) { $hcal.remove(); }
		$widget.append("<div id='hcalendar'></div>");
  
		this._hcalendar = new HotelCalendar('#hcalendar', options, pricelist, this.$el[0]);
		this._hcalendar.addEventListener('hcOnChangeDate', function(ev){
			var date_begin = moment(ev.detail.newDate);
			var days = self._hcalendar.getOptions('days')-1;
			var date_end = date_begin.clone().add(days, 'd');
			
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			self.reload_hcalendar_reservations();
		});
		this._hcalendar.addEventListener('hcalOnMouseEnterReservation', function(ev){
			var tp = self._reserv_tooltips[ev.detail.reservationObj.id];
			var arrival_hour = moment.utc(tp[2]).local().format('HH:mm');
			
			var qdict = {
				'name': tp[0],
				'phone': tp[1],
				'arrival_hour': arrival_hour
			};
			
			$(ev.detail.reservationDiv).tooltip({
				animation: true,
				html: true,
				placement: 'bottom',
				title: QWeb.render('HotelCalendar.Tooltip', qdict)
			}).tooltip('show');
		});
		this._hcalendar.addEventListener('hcalOnContextMenuReservation', function(ev){
			var res_id = ev.detail.reservationObj.getUserData('folio_id');
			self._model.call('get_formview_id', [res_id, Session.user_context]).then(function(view_id){
				var pop = new Common.FormViewDialog(self, {
	                res_model: 'hotel.folio',
	                res_id: res_id,
	                title: _t("Open: ") + ev.detail.reservationObj.title,
	                view_id: view_id,
	                //readonly: false
	            }).open();
				pop.on('write_completed', self, function(){
                    self.trigger('changed_value');
                });
				pop.on('closed', self, function(){
                    self.reload_hcalendar_reservations(); // Here because don't trigger 'write_completed' when change state to confirm
                });
			});
		});
		this._hcalendar.addEventListener('hcalOnChangeReservation', function(ev){
			var newReservation = ev.detail.newReserv;
			var oldReservation = ev.detail.oldReserv;
			var folio_id = newReservation.getUserData('folio_id');
			
			var reservs = self._hcalendar.getReservations(newReservation);
			var linkedReservs = _.find(reservs, function(item){ 
				return (item.getUserData('folio_id') === folio_id);
			});
			
			var qdict = {
	            ncheckin: newReservation.startDate.format(L10N_DATETIME_MOMENT_FORMAT),
	            ncheckout: newReservation.endDate.format(L10N_DATETIME_MOMENT_FORMAT),
	            nroom: newReservation.room.number,
	            ocheckin: oldReservation.startDate.format(L10N_DATETIME_MOMENT_FORMAT),
	            ocheckout: oldReservation.endDate.format(L10N_DATETIME_MOMENT_FORMAT),
	            oroom: oldReservation.room.number,
	            hasReservesLinked: (linkedReservs && linkedReservs.length != 0)?true:false
	        };
			new Dialog(self, {
                title: _t("Confirm Reservation Changes"),
                buttons: [
                	{
                		text: _t("Yes, change it"),
                		classes: 'btn-primary',
                		close: true,
                		disabled: !newReservation.id,
                		click: function () {
                			var write_values = {
                				'checkin': newReservation.startDate.utc().format(ODOO_DATETIME_MOMENT_FORMAT),
                				'checkout': newReservation.endDate.utc().format(ODOO_DATETIME_MOMENT_FORMAT),
                				'product_id': newReservation.room.id
                			};
                			new Model('hotel.reservation').call('write', [[newReservation.id], write_values]).fail(function(err, ev){
                				self._hcalendar.swapReservation(newReservation, oldReservation);
                			});
                		}
                	}, 
                	{
                		text: _t("No"),
                		close: true,
                		click: function() {
                			self._hcalendar.swapReservation(newReservation, oldReservation);
                		}
                	}
                ],
                $content: QWeb.render('HotelCalendar.ConfirmReservationChanges', qdict)
            }).open();			
		});
		this._hcalendar.addEventListener('hcalOnChangeSelection', function(ev){
			var parentRow = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentRow}`);
			var parentCellStart = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentCell}`);
			var parentCellEnd = document.querySelector(`#${ev.detail.cellEnd.dataset.hcalParentCell}`);
			var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate).startOf('day').utc();
			var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate).endOf('day').utc();
			var room = self._hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
			var numBeds = room.shared?(ev.detail.cellEnd.dataset.hcalBedNum - ev.detail.cellStart.dataset.hcalBedNum)+1:room.capacity;
			
			if (numBeds <= 0) {
				return;
			}
			
			// Normalize Dates
			if (startDate.isAfter(endDate)) {
				var tt = endDate;
				endDate = startDate;
				startDate = tt;
			}
			
			// If start 'today' put the current hour
			var now = moment(new Date()).utc();
			if (startDate.isSame(now, 'day')) {
				startDate = now.add(30,'m'); // +30 mins
			}
			// Get Unit Price of Virtual Room
			self._model.call('get_vroom_price', [false, room.id, startDate.format(ODOO_DATETIME_MOMENT_FORMAT), endDate.format(ODOO_DATETIME_MOMENT_FORMAT)]).then(function(result){
				var reservation_lines = []
				for (var reserv of result['priceday']) {
					reservation_lines.push([0, false, reserv]);
				}
				var pop = new Common.FormViewDialog(this, {
                    res_model: 'hotel.folio',
                    context: {
                    	'default_adults': numBeds,
                    	'default_checkin': startDate.format(ODOO_DATETIME_MOMENT_FORMAT),
                    	'default_checkout': endDate.format(ODOO_DATETIME_MOMENT_FORMAT),
                    	'default_room_lines': [
                    		[0, false, {
                    			'checkin': startDate.format(ODOO_DATETIME_MOMENT_FORMAT),
                            	'checkout': endDate.format(ODOO_DATETIME_MOMENT_FORMAT),
                    			'adults': numBeds,
                    			'children': 0,
                    			'product_id': room.id,
                    			'product_uom': room.getUserData('uom_id'),
                    			'product_uom_qty': 1,
                    			//'product_uos': 1,
                    			'name': `${room.number}`,
                    			'reservation_lines': reservation_lines,
                    			'price_unit': result['total_price']
                    		}]
                    	]
                    },
                    title: _t("Create: ") + _t("Folio"),
                    initial_view: "form",
                    disable_multiple_selection: true,
                    form_view_options: { 'not_interactible_on_create':true },
                    create_function: function(data, options) {
                    	console.log("DATOS");
                    	console.log(data);
                        var def = $.Deferred();
                        var res = true;
                        var dataset = self.dataset;
                        options = options || {};
                        var internal_options = _.extend({}, options, {'internal_dataset_changed': true});
                        
                        self.mutex.exec(function(){
                        	return dataset.create(data, internal_options).then(function (id) {
                                dataset.ids.push(id);
                                res = id;
                            });
                        });
                        self.mutex.def.then(function () { 
                			var dialog = new Dialog(self, {
                                title: _t("Confirm Folio"),
                                buttons: [
                                	{
                                		text: _t("Yes, confirm it"),
                                		classes: 'btn-primary',
                                		close: true,
                                		disabled: res < 0,
                                		click: function () {
                                			self._model.call('action_confirm', [res]).then(function(results){
                                				self.generate_hotel_calendar();
                                			}).fail(function(err, ev){
                                				alert(_t("[Hotel Calendar]\nERROR: Can't confirm folio!"));
                                			});
                                		}
                                	}, 
                                	{
                                		text: _t("No"),
                                		close: true
                                	}
                                ],
                                $content: QWeb.render('HotelCalendar.ConfirmFolio')
                            }).open();
                			dialog.on("closed", null, function(){
                                self.trigger("change:commands", options);
                                def.resolve(res);
                			});
                        });
                        
                        return def;
                    },
                    read_function: function(ids, fields, options) {
                    	return self.dataset.read_ids(ids, fields, options);
                    },
                    on_selected: function() {
                        self.generate_hotel_calendar();
                    }
                }).open();
				
				console.log(pop);
			});	
		});
		
		this._hcalendar.addEventListener('hcalOnChangeRoomTypePrice', function(ev){
			var qdict = {
				'date':  ev.detail.date.local().format(L10N_DATE_MOMENT_FORMAT),
				'old_price': ev.detail.old_price,
				'new_price': ev.detail.price
			};
			new Dialog(self, {
                title: _t("Confirm Price Change"),
                buttons: [
                	{
                		text: _t("Yes, change it"),
                		classes: 'btn-primary',
                		close: true,
                		disabled: !ev.detail.date,
                		click: function () {
                			var categ_id = self._hcalendar.getRoomsByType(ev.detail.room_type)[0].getUserData('categ_id');
                			var data = {
                				'pricelist_id': PUBLIC_PRICELIST_ID,
                				'applied_on': '2_product_category',
                				'categ_id': categ_id,
                				'compute_price': 'fixed',
                				'date_start': ev.detail.date.format(ODOO_DATETIME_MOMENT_FORMAT),
                				'date_end': ev.detail.date.format(ODOO_DATETIME_MOMENT_FORMAT),
                				'fixed_price': ev.detail.price,
                				'sequence': 0,
                			};
                			new Model('product.pricelist.item').call('create', [data]).fail(function(err, ev){
                				alert(_t("[Hotel Calendar]\nERROR: Can't update price!"));
                				self._hcalendar.setDetailPrice(ev.detail.room_type, ev.detail.date, ev.detail.old_price);
                			});
                		}
                	}, 
                	{
                		text: _t("No"),
                		close: true,
                		click: function() {
                			self._hcalendar.setDetailPrice(ev.detail.room_type, ev.detail.date, ev.detail.old_price);
                		}
                	}
                ],
                $content: QWeb.render('HotelCalendar.ConfirmPriceChange', qdict)
            }).open();
		});
    },
    
    generate_hotel_calendar: function(){
    	var self = this;
    	
    	/** DO MAGIC **/
    	var domains = this.generate_domains();
    	var full_domain = [false, domains['dates'][0], domains['dates'][1], domains['rooms'] || [], domains['reservations'] || []];
    	this._model.call('get_hcalendar_data', full_domain).then(function(results){
    		self._reserv_tooltips = results['tooltips'];
			var rooms = [];
			for (var r of results['rooms']) {
				var nroom = new HRoom(
					r[0], // Id
					r[1], // Name
					r[2], // Capacity
					r[4], // Category
					r[5]  // Shared Room
				);
				nroom.addUserData({
					'categ_id': r[3],
					'uom_id': r[6]
				});
				rooms.push(nroom);
			}
			
			self.create_calendar({
				rooms: rooms,
				showPaginator: false
			}, results['pricelist']);
			
			var reservs = [];
			for (var r of results['reservations']) {
				var room = self._hcalendar.getRoom(r[0]);
				var nreserv = new HReservation(
					r[1], // Id
					room, // Room
					r[2], // Title
					r[3], // Adults
					r[4], // Childrens
					moment.utc(r[5]).local(), // Date Start
					moment.utc(r[6]).local(), // Date End
					r[8], // Color
					r[9] || false // Read Only
				);
				nreserv.addUserData({'folio_id': r[7]});
				reservs.push(nreserv);
			}
			self._hcalendar.setReservations(reservs);
		});
    },
    
    call_action: function(action) {
    	this._action_manager.do_action(action);
    },
    
    update_buttons_counter: function() {
    	var self = this;
    	var domain = [];

    	 // Checkouts Button
        domain = [['room_lines.checkout', '>=', moment().startOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)],
            ['room_lines.checkout','<=', moment().endOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)],
            ];
        this._model.call('search_count', [domain]).then(function(count){
            var $ninfo = $this.$el.find('#pms-menu #btn_action_checkout div.ninfo');
            var $badge_checkout = $ninfo.find('.badge');
            if (count > 0) {
                $badge_checkout.text(count);
                $badge_checkout.parent().show();
                $ninfo.show();
            } else {
                $ninfo.hide();
            }
        });

        // Checkins Button
        domain = [['room_lines.checkin', '>=', moment().startOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)],
                        ['room_lines.checkin','<=', moment().endOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)],
                        ];
        this._model.call('search_count', [domain]).then(function(count){
            var $ninfo = $this.$el.find('#pms-menu #btn_action_checkin div.ninfo');
            var $badge_checkin = $ninfo.find('.badge');
            if (count > 0) {
                $badge_checkin.text(count);
                $badge_checkin.parent().show();
                $ninfo.show();
            } else {
                $ninfo.hide();
            }
        });

        // Charges Button
        //domain = [['invoice_ids.residual','>',0 ],['room_lines.checkin','<=', moment().endOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)]];

        //var $badge_charges = this.$el.find('#pms-menu #btn_action_paydue .badge');
    //new Model('hotel.folio').call('search_count', [domain]).then(function(count){
        //if (count > 0) {
          //  $badge_charges.text(count);
            //    $badge_charges.parent().show();
            //}
      //  });
    },
    
    init_calendar_view: function(){
    	var self = this;

		/** HACKISH ODOO VIEW **/
        //this._action_manager.main_control_panel.$el.hide();
		$(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
		//this.$el.parent().parent().css('overflow', 'none');
		
		/** VIEW CONTROLS INITIALIZATION **/
		// DATE TIME PICKERS
		var DTPickerOptions = { 
			viewMode: 'months',
			icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            format : L10N_DATE_MOMENT_FORMAT,
		};
		var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
		var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
		$dateTimePickerBegin.datetimepicker(DTPickerOptions);
		$dateTimePickerEnd.datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));
		$dateTimePickerBegin.on("dp.change", function (e) {
			$dateTimePickerEnd.data("DateTimePicker").setMinDate(e.date.add(3,'d'));
			$dateTimePickerEnd.data("DateTimePicker").setMaxDate(e.date.add(2,'M'));
			self.on_change_filter_date(e, true);
	    });
		$dateTimePickerEnd.on("dp.change", function (e) {
			self.on_change_filter_date(e, false);
	    });
		//this.$el.find('#pms-search #cal-pag-selector').datetimepicker($.extend({}, DTPickerOptions, { 
		//	'useCurrent': true,
		//}));
		
		//var $dateTimePickerSelector = this.$el.find('#pms-search #cal-pag-selector-calendar');		
		//$dateTimePickerSelector.datetimepicker($.extend({}, DTPickerOptions, {'inline':true, 'sideBySide': false}));
		//$dateTimePickerSelector.on("dp.change", function (e) {
		//	console.log(e);
			/*var date_begin = moment(this.data("DateTimePicker").getDate());
			var days = moment(date_begin).daysInMonth();
			var date_end = date_begin.clone().add(days, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);*/
	    //});
		
        var date_begin = moment().startOf('day');
		var days = moment(date_begin).daysInMonth();
		var date_end = date_begin.clone().add(days, 'd').endOf('day');
		$dateTimePickerBegin.data("ignore_onchange", true);
		$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
		$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
		
		// View Events
		this.$el.find("#pms-search #search_query").on('change', function(ev){
			self.reload_hcalendar_reservations();
		});
		this.$el.find("#pms-search #cal-pag-prev-plus").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(15, 'd').startOf('day');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(15, 'd').endOf('day');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-prev").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(1, 'd').startOf('day');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(1, 'd').endOf('day');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next-plus").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(15, 'd').startOf('day');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(15, 'd').endOf('day');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(1, 'd').startOf('day');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(1, 'd').endOf('day');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-selector").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
			var date_begin = moment().startOf('day');
			var days = moment(date_begin).daysInMonth();
			var date_end = date_begin.clone().add(days, 'd').endOf('day');
			$dateTimePickerBegin.data("ignore_onchange", true);
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		
		/* BUTTONS */
		this.update_buttons_counter();
		this.$el.find("#btn_action_checkout").on('click', function(ev){
			self.call_action('hotel_calendar.hotel_reservation_action_checkout');
		});
		this.$el.find("#btn_action_checkin").on('click', function(ev){
			self.call_action('hotel_calendar.hotel_reservation_action_checkin');
		});
		this.$el.find("#btn_action_paydue").on('click', function(ev){
			self.call_action('hotel_calendar.hotel_reservation_action_paydue');
		});
		this.$el.find("#btn_action_refresh").on('click', function(ev){
			window.location.reload();
		});
		
    	/** RENDER CALENDAR **/
		this.generate_hotel_calendar();
		
		/** DATABASE QUERIES **/
		// Get Types
		new Model('hotel.room.type').query(['cat_id','name']).all().then(function(resultsHotelRoomType){
			var $list = self.$el.find('#pms-search #type_list');
			$list.html('');
			resultsHotelRoomType.forEach(function(item, index){
				$list.append(`<option value="${item.cat_id[0]}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				self.generate_hotel_calendar();
			});
		});
		// Get Floors
		new Model('hotel.floor').query(['id','name']).all().then(function(resultsHotelFloor){
			var $list = self.$el.find('#pms-search #floor_list');
			$list.html('');
			resultsHotelFloor.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				self.generate_hotel_calendar();
			});
		});
		// Get Amenities
		new Model('hotel.room.amenities').query(['id','name']).all().then(function(resultsHotelRoomAmenities){
			var $list = self.$el.find('#pms-search #amenities_list');
			$list.html('');
			resultsHotelRoomAmenities.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				self.generate_hotel_calendar();
			});
		});
		// Get Virtual Rooms
		new Model('hotel.virtual.room').query(['id','name']).all().then(function(resultsHotelVirtualRooms){
			var $list = self.$el.find('#pms-search #virtual_list');
			$list.html('');
			resultsHotelVirtualRooms.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				self.generate_hotel_calendar();
			});
		});
		
		return $.when();
    },
    
    on_change_filter_date: function(ev, isStartDate) {
    	isStartDate = isStartDate || false;
    	var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
		var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
		
		// FIXME: Hackish onchange ignore (Used when change dates from code)
		if ($dateTimePickerBegin.data("ignore_onchange") || $dateTimePickerEnd.data("ignore_onchange")) {
			$dateTimePickerBegin.data("ignore_onchange", false);
			$dateTimePickerEnd.data("ignore_onchange", false)
			return true;
		}
		
		var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate();
		var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate();
    	if (date_begin && date_end && date_begin.isBefore(date_end) && this._hcalendar) {
    		var days = isStartDate?date_begin.daysInMonth():date_end.diff(date_begin,'days')+1;
    		this._hcalendar.setStartDate(date_begin, days);
    		this.reload_hcalendar_reservations();
    	}
    },
    
    _on_bus_signal: function(notifications) {
    	var need_reload = false;
    	for (var notif of notifications) {
    		console.log(notif);
    		if (notif[0][1] === 'hotel.reservation' && notif[1]['type'] === "reservation") {
    			if (notif[1]['subtype'] === "create") {
    				this.do_notify(_t("Reservation Created"), `Name: ${notif[1]['name']}`, true);
    			} else if (notif[1]['subtype'] === "write") {
    				this.do_notify(_t("Reservation Changed"), `Name: ${notif[1]['name']}`, true);
    			} else if (notif[1]['subtype'] === "unlink") {
    				this.do_notify(_t("Reservation Deleted"), `Name: ${notif[1]['name']}`, true);
    			}
    			need_reload = true;
    		}
    	}
    	if (need_reload) {
    		this.reload_hcalendar_reservations();
    	}
    },
    
    reload_hcalendar_reservations: function() {
    	var self = this;
    	var domains = this.generate_domains();
    	var full_domain = [false, domains['dates'][0], domains['dates'][1], domains['rooms'] || [], domains['reservations'] || [], false];
    	this._model.call('get_hcalendar_data', full_domain).then(function(results){
    		self._reserv_tooltips = results['tooltips'];
    		var reservs = [];
			for (var r of results['reservations']) {
				var room = self._hcalendar.getRoom(r[0]);
				var nreserv = new HReservation(
					r[1], // Id
					room, // Room
					r[2], // Title
					r[3], // Adults
					r[4], // Childrens
					moment.utc(r[5]).local(), // Date Start
					moment.utc(r[6]).local(), // Date End
					r[8], // Color
					r[9] || false // Read Only
				);
				nreserv.addUserData({'folio_id': r[7]});
				reservs.push(nreserv);
			}
			
			self._hcalendar.pricelist = results['pricelist'];
			self._hcalendar.setReservations(reservs);
		});
    	this.update_buttons_counter();
    },
    
    generate_domains: function() {
    	var domainRooms = [];
    	var category = this.$el.find('#pms-search #type_list').val();
    	if (category) { domainRooms.push(['categ_id.id', 'in', category]); }
    	var floor = this.$el.find('#pms-search #floor_list').val();
    	if (floor) { domainRooms.push(['floor_id.id', 'in', floor]); }
    	var amenities = this.$el.find('#pms-search #amenities_list').val();
    	if (amenities) { domainRooms.push(['room_amenities.id', 'in', amenities]); }
    	var virtual = this.$el.find('#pms-search #virtual_list').val();
    	if (virtual) { domainRooms.push(['virtual_rooms.id', 'in', virtual]); }
    	
    	var domainReservations = [];
    	var search_query = this.$el.find('#pms-search #search_query').val();
    	if (search_query) {
    		domainReservations.push('|');
    		domainReservations.push('|');
    		domainReservations.push(['partner_id.name', 'ilike', search_query]);
    		domainReservations.push(['partner_id.phone', 'ilike', search_query]);
    		domainReservations.push(['partner_id.mobile', 'ilike', search_query]);
    	}
    	
    	var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
		var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
	
    	var date_begin = moment($dateTimePickerBegin.data("DateTimePicker").getDate()).startOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT);
    	var date_end = moment($dateTimePickerEnd.data("DateTimePicker").getDate()).endOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT);

    	return {
    		'rooms': domainRooms,
    		'reservations': domainReservations,
    		'dates': [date_begin, date_end]
    	};
    }
});

Core.view_registry.add('pms', HotelCalendarView);
return HotelCalendarView;

});

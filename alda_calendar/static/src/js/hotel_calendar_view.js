odoo.define('alda_calendar.HotelCalendarView', function (require) {
"use strict";
/*
 * Hotel Calendar View
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */

var core = require('web.core');
//var data = require('web.data');
var time = require('web.time');
var Model = require('web.DataModel');
var View = require('web.View');
//var pyeval = require('web.pyeval');
//var ActionManager = require('web.ActionManager');

var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;

var HotelCalendarView = View.extend({
	/** VIEW OPTIONS **/
	template: "HotelCalendarView",
    display_name: _lt('Hotel Calendar'),
    icon: 'fa fa-map-marker',
    view_type: "pms",
    _model: null,
    // Custom Options
    hcalendar: null,

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
        this._model = new Model(this.dataset.model);
    },    

    view_loading: function(r) {
        return this.load_custom_view(r);
    },

    destroy: function () {
    	this._super.apply(this, arguments);
    },

    load_custom_view: function(fv) {
    	/* xml view calendar options */
        var attrs = fv.arch.attrs,
            self = this;
        this.fields_view = fv;
        //this.$calendar = $(QWeb.render("HotelCalendarView"));
        //this.$el.append(this.$calendar);
        
        var edit_check = new Model(this.dataset.model)
        	.call("check_access_rights", ["write", false])
        	.then(function (write_right) {
        		self.write_right = write_right;
        	});
	    var init = new Model(this.dataset.model)
	        .call("check_access_rights", ["create", false])
	        .then(function (create_right) {
	            self.create_right = create_right;
	            self.init_hotel_calendar().then(function() {
	                $(window).trigger('resize');
	                self.trigger('hotel_calendar_view_loaded', fv);
	                self.ready.resolve();
	            });
	        });
	    return $.when(edit_check, init);
    },
    
    do_show: function() {
        if (this.$calendar) {
            this.$calendar.show();
        }
        this.do_push_state({});
        return this._super();
    },
    do_hide: function () {
        if (this.$calendar) {
            this.$calendar.hide();
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
        if (this.$buttons) {
            this.$buttons.off();
        }
        
        $(document).find('.oe-control-panel').show();
        
        return this._super.apply(this, arguments);
    },
    
    /** CUSTOM METHODS **/
    create_calendar: function(options) {
    	var $this = this;
    	// CALENDAR
		this.hcalendar = new HotelCalendar('#hcalendar', options, null, this.$el[0]);
		this.$el.find("#pms-search #cal-pag-prev-plus").on('click', function(ev){
			$this.hcalendar.back($this.hcalendar.options.days, 'd');
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-prev").on('click', function(ev){
			$this.hcalendar.back('1', 'd');
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next-plus").on('click', function(ev){
			$this.hcalendar.advance($this.hcalendar.options.days, 'd');
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next").on('click', function(ev){
			$this.hcalendar.advance('1', 'd');
			ev.preventDefault();
		});
    },
    
    init_hotel_calendar: function(domain){
    	/*this._model.call('get_reservations_data', [domain]).then(function(results){
			console.log(results);
		});*/
    	var $this = this;
    	
    	// Get Rooms
		new Model('hotel.room').query(['id','name','capacity','categ_id', 'shared_room']).all().then(function(resultsHotelRoom){
			var rooms = [];
			resultsHotelRoom.forEach(function(item, index){
				rooms.push(new HRoom(item.name, item.capacity, item.categ_id[1], item.shared_room));
			});
			
			var options = {
				rooms: rooms,
				showPaginator: false,
			};
			$this.create_calendar(options);
			
			// Get Reservations
			new Model('hotel.reservation').query(['reservation_line','adults','children','partner_id','checkin','checkout']).all().then(function(resultsHotelReservations){
				var reservs = resultsHotelReservations;
				var reservations = [];
				reservs.forEach(function(itemReserv, indexReserv){
					new Model('hotel_reservation.line').query(['reserve']).filter([['id', 'in', itemReserv.reservation_line]]).all().then(function(resultsHotelReservationLine){
						resultsHotelReservationLine.forEach(function(itemHotelRervationLine, indexHoteResevationLine){
							resultsHotelRoom.forEach(function(itemRoom, indexRoom){
								if (itemHotelRervationLine.reserve.includes(itemRoom.id)) {
									var room = $this.hcalendar.getRoom(itemRoom.name);
									var nres = new HReservation(room, itemReserv.partner_id[1], itemReserv.adults+itemReserv.children);
									nres.setStartDate(itemReserv.checkin);
									nres.setEndDate(itemReserv.checkout);
									reservations.push(nres);
								}
							});
						});
						$this.hcalendar.setReservations(reservations);
					});
				});
			});
		});

		/** HACKISH ODOO VIEW **/
		$(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
		$(document).find('.oe-control-panel').hide(); // Remove "control panel" in the view
		
		/** VIEW CONTROLS INITIALIZATION **/
		// DATE TIME PICKERS
		var $this = this;
		var l10n = _t.database.parameters;
		var DTPickerOptions = { 
			viewMode: 'months',
			icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down'
               },
            language : moment.locale(),
            format : time.strftime_to_moment_format(l10n.date_format),
		};
		this.$el.find('#pms-search #date_begin').datetimepicker(DTPickerOptions);
		this.$el.find('#pms-search #date_end').datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));
		this.$el.find("#pms-search #date_begin").on("dp.change", function (e) {
	        $this.$el.find('#pms-search #date_end').data("DateTimePicker").setMinDate(e.date);
	    });
		this.$el.find("#pms-search #date_end").on("dp.change", function (e) {
	        $this.$el.find('#pms-search #date_begin').data("DateTimePicker").setMaxDate(e.date);
	    });
		//this.$el.find('#pms-search #cal-pag-selector').datetimepicker($.extend({}, DTPickerOptions, { 
		//	'useCurrent': true,
		//}));
		
		// Get Types
		new Model('hotel.room.type').query(['id','name']).all().then(function(resultsHotelRoomType){
			var $list = $this.$el.find('#pms-search #type_list');
			$list.html('');
			resultsHotelRoomType.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
		});
		// Get Floors
		new Model('hotel.floor').query(['id','name']).all().then(function(resultsHotelFloor){
			var $list = $this.$el.find('#pms-search #floor_list');
			$list.html('');
			resultsHotelFloor.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
		});
		// Get Amenities
		new Model('hotel.room.amenities').query(['id','name']).all().then(function(resultsHotelRoomAmenities){
			var $list = $this.$el.find('#pms-search #amenities_list');
			$list.html('');
			resultsHotelRoomAmenities.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
		});
		
		return $.when();
    }
});

core.view_registry.add('pms', HotelCalendarView);
return HotelCalendarView;

});

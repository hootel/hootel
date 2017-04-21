odoo.define('alda_calendar.HotelCalendarView', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var time = require('web.time');
var Model = require('web.DataModel');
var View = require('web.View');
var pyeval = require('web.pyeval');
var ActionManager = require('web.ActionManager');
var HotelCalendarJS = require('alda_calendar.HotelCalendarJS');

var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;

var HotelCalendarView = View.extend({
	template: "HotelCalendarView",
    display_name: _lt('Hotel Calendar'),
    icon: 'fa fa-map-marker',
    view_type: "pms",
    _model: null,
    hcalendar: null,

    init: function(parent, dataset, view_id, options) {
    	console.info("ss2");
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
    
    create_calendar: function(options) {
    	var $this = this;
    	// CALENDAR
		this.hcalendar = new HotelCalendarJS('#hcalendar', options, null, this.$el[0]);
		this.$el.find("#pms-search #cal-pag-prev-plus").on('click', function(ev){
			$this.hcalendar.back('15', 'd');
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-prev").on('click', function(ev){
			$this.hcalendar.back('1', 'd');
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next-plus").on('click', function(ev){
			$this.hcalendar.advance('15', 'd');
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
		new Model('hotel.room').call('search_read', [[]]).then(function(results){
			var rooms = {}
			for (var index in results) {
				var room = results[index];
				rooms[room.name] = {
					persons: room.capacity,
					shared: room.shared_room,
					type: room.categ_id[1]
				};
			}
			
			var options = {
				rooms: rooms,
				showPaginator: false,
			};
			$this.create_calendar(options);
			
			// Get Reservations
			new Model('hotel.reservation').call('search_read', [[]]).then(function(results){
				console.log("RESERVAS");
				console.log(results);
				var reservation_lines = [];
				for (var item in results) {
					reservation_lines = reservation_lines.concat(results[item].reservation_line);
				}
				console.log(reservation_lines);
				var reservs = results;
				new Model('hotel.room').query(['id','name','categ_id']).filter([["id", "in", reservation_lines]]).all().then(function(resultsR){
					console.log("OBOOM");
					console.log(resultsR);
					
					var reservations = [];
					for (var item in resultsR){
						for (var itemB in results){
							var room = resultsR[item];
							var reserv = results[itemB];
							if (reserv.reservation_line.includes(room.id)) {
								reservations.push({
									room_type: room.categ_id[1],
									room_number: room.name,
									room_persons: reserv.adults+reserv.children,
									start_date: moment(reserv.checkin).format("DD/MM/YYYY"),
									end_date: moment(reserv.checkout).format("DD/MM/YYYY"),
									title: reserv.partner_id[1]
								});
							}
						}
					}
					console.log("RESERVAS");
					console.log(reservations);
					$this.hcalendar.setReservations(reservations);
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
		
		// Get Type
		new Model('hotel.room.type').query(['name']).all().then(function(results){
			var $list = $this.$el.find('#pms-search #type_list');
			$list.html('');
			for (var index in results) {
				$list.append(`<div class="checkbox"><label><input type="checkbox" value="${results[index].name}" />${results[index].name}</label></div>`);
			}
		});
		// Get Floors
		new Model('hotel.floor').query(['name']).all().then(function(results){
			var $list = $this.$el.find('#pms-search #floor_list');
			$list.html('');
			for (var index in results) {
				$list.append(`<div class="checkbox"><label><input type="checkbox" value="${results[index].name}" />${results[index].name}</label></div>`);
			}
		});
		// Get Amenities
		new Model('hotel.room.amenities').query(['name']).all().then(function(results){
			var $list = $this.$el.find('#pms-search #amenities_list');
			$list.html('');
			for (var index in results) {
				$list.append(`<div class="checkbox"><label><input type="checkbox" value="${results[index].name}" />${results[index].name}</label></div>`);
			}
		});
		
		return $.when();
    }
});

core.view_registry.add('pms', HotelCalendarView);
return HotelCalendarView;

});

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
var common = require('web.form_common');
//var pyeval = require('web.pyeval');
var ActionManager = require('web.ActionManager');

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
    reserv_tooltips: {},
    action_manager: null,
    date_begin: null,
    date_end: null,

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
        this.action_manager = this.findAncestor(function(ancestor){ return ancestor instanceof ActionManager });
        
        this.date_begin = moment(new Date()).subtract('1','d');
		var days = moment(this.date_begin).daysInMonth()+1;
		this.date_end = this.date_begin.clone().add(days, 'd');
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
	            self.init_calendar_view().then(function() {
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
    	if (this.hcalendar) {
    		delete this.hcalendar;
    	}
		var $widget = this.$el.find("#hcal_widget");
		var $hcal = $widget.find('#hcalendar');
		if ($hcal) { $hcal.remove(); }
		$widget.append("<div id='hcalendar'></div>");
  
		this.hcalendar = new HotelCalendar('#hcalendar', options, null, this.$el[0]);
		this.hcalendar.addEventListener('hcOnChangeDate', function(ev){
			$this.date_begin = ev.detail.newDate;
			var days = moment($this.date_begin || new Date()).daysInMonth()+1;
			$this.date_end = $this.date_begin.clone().add(days, 'd');
			$this.reload_hcalendar_widget();
		});
		this.hcalendar.addEventListener('hcalOnMouseEnterReservation', function(ev){
			var tp = $this.reserv_tooltips[ev.detail.reservationObj.id];
			var arrival_hour = moment(moment.utc(tp[2]).toDate()).format('HH:mm:ss'); // UTC -> Local Time
			$(ev.detail.reservationDiv).tooltip({
				animation: true,
				html: true,
				placement: 'bottom',
				title: `<b>${_t('Name:')}</b> ${tp[0]}<br/><b>${_t('Phone:')}</b> ${tp[1]}<br/><b>${_t('Arrival Hour:')}</b> ${arrival_hour}`,
			}).tooltip('show');
		});
		this.hcalendar.addEventListener('hcalOnContextMenuReservation', function(ev){
			var res_id = ev.detail.reservationObj.id;
			$this._model.call('get_formview_id', [res_id]).then(function(view_id){
				var pop = new common.FormViewDialog($this, {
	                res_model: 'hotel.reservation',
	                res_id: res_id,
	                title: _t("Open: ") + ev.detail.reservationObj.title,
	                view_id: view_id,
	                readonly: false
	            }).open();
				pop.on('write_completed', self, function(){
					$this.reload_hcalendar_widget();
                    $this.trigger('changed_value');
                });
			});
		});
		this.hcalendar.addEventListener('hcalOnChangeReservation', function(ev){
			var newReservation = ev.detail.new;
			var oldReservation = ev.detail.old;
			
			if (!confirm("¿Estás seguro/a?")) {
				$this.hcalendar.swapReservation(newReservation, oldReservation);
				return;
			}
			
			var linkedReservations = $this.hcalendar.getLinkedReservations(newReservation).concat(newReservation);
			var x2xCommands = [];
			for (var r of linkedReservations) {
				var room = $this.hcalendar.getRoom(r.room.id);
				x2xCommands.push([1, r.getUserData('reservation_line_id'), {
        			//'adults': r.adults,
        			//'children': r.childrens,
        			'categ_id': r.room.getUserData('categ_id'),
        			'name': false,
        			'reserve': [[6, false, [r.room.id]]]
        		}]);
			}

			var write_values = {
				// TODO: Revisar porque falla con formato UTC
				'checkin': newReservation.startDate.format("YYYY-MM-DD HH:mm:ss"),
				'checkout': newReservation.endDate.format("YYYY-MM-DD HH:mm:ss"),
				'reservation_line': x2xCommands
			};
			new Model('hotel.reservation').call('write', [[newReservation.id], write_values]).fail(function(err, ev){
				$this.hcalendar.swapReservation(newReservation, oldReservation);
			});
		});
		this.hcalendar.addEventListener('hcalOnChangeSelection', function(ev){
			var parentRow = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentRow}`);
			var parentCellStart = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentCell}`);
			var parentCellEnd = document.querySelector(`#${ev.detail.cellEnd.dataset.hcalParentCell}`);
			var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate).utc().format("YYYY-MM-DD HH:mm:ss");
			var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate).utc().format("YYYY-MM-DD HH:mm:ss");
			var room = $this.hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
			
			$this._model.call('get_formview_id', [false]).then(function(view_id){
				new common.SelectCreateDialog(this, {
	                res_model: 'hotel.reservation',
	                context: {
	                	'default_checkin': startDate,
	                	'default_checkout': endDate,
	                	'default_reservation_line': [
	                		[0, false, {
	                			'adults': 0,
	                			'children': 0,
	                			'categ_id': room.getUserData('categ_id'),
	                			'name': false,
	                			'reserve': [[6, false, [room.id]]]
	                		}]
	                	]
	                },
	                title: _t("Create: ") + _t("Reservation"),
	                initial_view: "form",
	                create_function: function(data, options) {
	                    var def = $.Deferred();
	                    var dataset = $this.dataset;
	                    options = options || {};
	                    var internal_options = _.extend({}, options, {'internal_dataset_changed': true});
	                    return dataset.create(data, internal_options).then(function (id) {
	                        dataset.ids.push(id);
	                    });
	                },
	                read_function: function(ids, fields, options) {
	                	return $this.dataset.read_ids(ids, fields, options);
	                },
	                parent_view: view_id,
	                form_view_options: {'not_interactible_on_create':true},
	                on_selected: function() {
	                    $this.reload_hcalendar_widget();
	                }
	            }).open();
			});
		});
		
		
		// View Events
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
    
    generate_hotel_calendar: function(domainRooms, domainReservations){
    	var $this = this;
    	domainRooms = domainRooms || [];
    	domainReservations = domainReservations || [];
    	
    	/** DO MAGIC **/
    	this._model.call('get_hcalendar_data', [false, domainRooms, domainReservations]).then(function(results){
    		$this.reserv_tooltips = results['tooltips'];
			var rooms = [];
			for (var r of results['rooms']) {
				var nroom = new HRoom(
					r[0], // Id
					r[1], // Name
					r[2], // Capacity
					r[4], // Category
					r[5]  // Shared Room
				);
				nroom.addUserData({'categ_id': r[3]});
				rooms.push(nroom);
			}
			
			$this.create_calendar({
				rooms: rooms,
				showPaginator: false
			});
			
			var reservs = [];
			for (var r of results['reservations']) {
				var room = $this.hcalendar.getRoom(r[0]);
				var nreserv = new HReservation(
					r[1], // Id
					room, // Room
					r[2], // Title
					r[3], // Adults
					r[4], // Childrens
					moment.utc(r[5]).toDate(), // Date Start
					moment.utc(r[6]).toDate(), // Date End
				);
				nreserv.addUserData({'reservation_line_id': r[7]});
				reservs.push(nreserv);
			}
			$this.hcalendar.setReservations(reservs);
		});
    },
    
    init_calendar_view: function(){
    	var $this = this;

		/** HACKISH ODOO VIEW **/
		$(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
		$(document).find('.oe-control-panel').hide(); // Remove "control panel" in the view
		
		/** VIEW CONTROLS INITIALIZATION **/
		// DATE TIME PICKERS
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
		var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
		var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
		$dateTimePickerBegin.datetimepicker(DTPickerOptions);
		$dateTimePickerEnd.datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));
		$dateTimePickerBegin.on("dp.change", function (e) {
			$dateTimePickerEnd.data("DateTimePicker").setMinDate(e.date);
			$this.reload_hcalendar_widget();
	    });
		$dateTimePickerEnd.on("dp.change", function (e) {
			$dateTimePickerBegin.data("DateTimePicker").setMaxDate(e.date);
			$this.reload_hcalendar_widget();
	    });
		//this.$el.find('#pms-search #cal-pag-selector').datetimepicker($.extend({}, DTPickerOptions, { 
		//	'useCurrent': true,
		//}));
		
    	/** RENDER CALENDAR **/
		this.reload_hcalendar_widget();
		
		/** DATABASE QUERIES **/
		// Get Types
		new Model('hotel.room.type').query(['cat_id','name']).all().then(function(resultsHotelRoomType){
			var $list = $this.$el.find('#pms-search #type_list');
			$list.html('');
			resultsHotelRoomType.forEach(function(item, index){
				$list.append(`<option value="${item.cat_id[0]}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				$this.reload_hcalendar_widget();
			});
		});
		// Get Floors
		new Model('hotel.floor').query(['id','name']).all().then(function(resultsHotelFloor){
			var $list = $this.$el.find('#pms-search #floor_list');
			$list.html('');
			resultsHotelFloor.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				$this.reload_hcalendar_widget();
			});
		});
		// Get Amenities
		new Model('hotel.room.amenities').query(['id','name']).all().then(function(resultsHotelRoomAmenities){
			var $list = $this.$el.find('#pms-search #amenities_list');
			$list.html('');
			resultsHotelRoomAmenities.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				$this.reload_hcalendar_widget();
			});
		});
		// Get Virtual Rooms
		new Model('hotel.virtual.room').query(['id','name']).all().then(function(resultsHotelVirtualRooms){
			var $list = $this.$el.find('#pms-search #virtual_list');
			$list.html('');
			resultsHotelVirtualRooms.forEach(function(item, index){
				$list.append(`<option value="${item.id}">${item.name}</option>`);
			});
			$list.select2();
			$list.on('change', function(ev){
				$this.reload_hcalendar_widget();
			});
		});
		
		return $.when();
    },
    
    reload_hcalendar_widget: function() {
    	var domains = this.generate_domains();
		this.generate_hotel_calendar(domains['rooms'], domains['reservations']);
    },
    
    generate_domains: function() {
    	var domainRooms = [];
    	var category = this.$el.find('#pms-search #type_list').val();
    	if (category) { domainRooms.push(['categ_id.id', 'in', category]); }
    	var floor = this.$el.find('#pms-search #floor_list').val();
    	if (floor) { domainRooms.push(['floor_id.id', 'in', floor]); }
    	var amenities = this.$el.find('#pms-search #amenities_list').val();
    	if (amenities) { domainRooms.push(['room_amenities.id', 'in', amenities]); }
    	//var virtual = this.$el.find('#pms-search #virtual_list').val();
    	//if (virtual) { domainVirtualRooms.push('id', 'in', virtual); }
    	
    	var domainReservations = [];    	
    	var date_begin = this.date_begin.format("YYYY-MM-DD HH:mm:ss");
    	if (date_begin) { domainReservations.push(['checkin', '>=', date_begin]); }
    	var date_end = this.date_end.format("YYYY-MM-DD HH:mm:ss");
    	if (date_end) { domainReservations.push(['checkout', '<=', date_end]); }
    	
    	return {'rooms':domainRooms, 'reservations':domainReservations};
    }
});

core.view_registry.add('pms', HotelCalendarView);
return HotelCalendarView;

});

odoo.define('alda_calendar.HotelCalendarView', function (require) {
"use strict";
/*
 * Hotel Calendar View
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */
/* TODO (TOFIX):
 *  1. When change date with filter buttons, the calendar reload two times because datetime-pickers updating.
 *        Easy to resolve if adds 'search' button instead use 'onchange' events.
 */

var core = require('web.core');
//var data = require('web.data');
var time = require('web.time');
var Model = require('web.DataModel');
var View = require('web.View');
var common = require('web.form_common');
//var pyeval = require('web.pyeval');
var ActionManager = require('web.ActionManager');
var utils = require('web.utils');

var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;

var PUBLIC_PRICELIST_ID = 1; // Hard-Coded public pricelist id

var HotelCalendarView = View.extend({
	/** VIEW OPTIONS **/
	template: "HotelCalendarView",
    display_name: _lt('Hotel Calendar'),
    icon: 'fa fa-map-marker',
    view_type: "pms",
    searchable: false,
    searchview_hidden: true,
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
        this.action_manager = this.findAncestor(function(ancestor){ return ancestor instanceof ActionManager; });
        this.mutex = new utils.Mutex();
    },    

    view_loading: function(r) {
        return this.load_custom_view(r);
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
        	$(document).find('.oe-control-panel').hide();
        	$widget.show();
        }
        this.do_push_state({});
        return this._super();
    },
    do_hide: function () {
    	var $widget = this.$el.find("#hcal_widget");
        if ($widget) {
        	$(document).find('.oe-control-panel').show();
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
        $(document).find('.oe-control-panel').show();
        return this._super.apply(this, arguments);
    },
    
    /** CUSTOM METHODS **/
    create_calendar: function(options, pricelist) {
    	var $this = this;
    	// CALENDAR
    	if (this.hcalendar) {
    		delete this.hcalendar;
    	}
		var $widget = this.$el.find("#hcal_widget");
		var $hcal = $widget.find('#hcalendar');
		if ($hcal) { $hcal.remove(); }
		$widget.append("<div id='hcalendar'></div>");
  
		this.hcalendar = new HotelCalendar('#hcalendar', options, pricelist, this.$el[0]);
		this.hcalendar.addEventListener('hcOnChangeDate', function(ev){
			var date_begin = moment(ev.detail.newDate);
			var days = $this.hcalendar.getOptions('days')-1;
			var date_end = date_begin.clone().add(days, 'd');
			
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			$this.reload_hcalendar_reservations();
		});
		this.hcalendar.addEventListener('hcalOnMouseEnterReservation', function(ev){
			var tp = $this.reserv_tooltips[ev.detail.reservationObj.id];
			var arrival_hour = moment.utc(tp[2]).local().format('HH:mm');
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
	                //readonly: false
	            }).open();
				pop.on('write_completed', $this, function(){
                    $this.trigger('changed_value');
                });
				pop.on('closed', $this, function(){
                    $this.reload_hcalendar_reservations(); // Here because don't trigger 'write_completed' when change state to confirm
                });
			});
		});
		this.hcalendar.addEventListener('hcalOnChangeReservation', function(ev){
			var newReservation = ev.detail.newReserv;
			var oldReservation = ev.detail.oldReserv;
			
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
				'checkin': newReservation.startDate.utc().format("YYYY-MM-DD HH:mm:ss"),
				'checkout': newReservation.endDate.utc().format("YYYY-MM-DD HH:mm:ss"),
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
			var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate).utc();
			var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate).utc();
			var room = $this.hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
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
			
			new common.SelectCreateDialog(this, {
                res_model: 'hotel.reservation',
                context: {
                	'default_adults': numBeds,
                	'default_checkin': startDate.format("YYYY-MM-DD HH:mm:ss"),
                	'default_checkout': endDate.format("YYYY-MM-DD HH:mm:ss"),
                	'default_reservation_line': [
                		[0, false, {
                			'adults': numBeds,
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
                    var res = true;
                    var dataset = $this.dataset;
                    options = options || {};
                    var internal_options = _.extend({}, options, {'internal_dataset_changed': true});
                    
                    $this.mutex.exec(function(){
                    	return dataset.create(data, internal_options).then(function (id) {
                            dataset.ids.push(id);
                            res = id;
                        });
                    });
                    $this.mutex.def.then(function () {
                        $this.trigger("change:commands", options);
                        def.resolve(res);
                    });
                    
                    return def;
                },
                read_function: function(ids, fields, options) {
                	return $this.dataset.read_ids(ids, fields, options);
                },
                on_selected: function() {
                    $this.generate_hotel_calendar();
                }
            }).open();
		});
		
		this.hcalendar.addEventListener('hcalOnChangeRoomTypePrice', function(ev){
			if (!confirm("¿Estás seguro/a?")) {
				$this.hcalendar.setDetailPrice(ev.detail.room_type, ev.detail.date, ev.detail.old_price);
				return;
			}
			console.log(ev.detail.date);
			var categ_id = $this.hcalendar.getRoomsByType(ev.detail.room_type)[0].getUserData('categ_id');
			var data = {
				'pricelist_id': PUBLIC_PRICELIST_ID,
				'applied_on': '2_product_category',
				'categ_id': categ_id,
				'compute_price': 'fixed',
				'date_start': moment(ev.detail.date, HotelCalendar.DATE_FORMAT_SHORT_).format('YYYY-MM-DD'),
				'date_end': moment(ev.detail.date, HotelCalendar.DATE_FORMAT_SHORT_).format('YYYY-MM-DD'),
				'fixed_price': ev.detail.price,
				'sequence': 0,
			};
			new Model('product.pricelist.item').call('create', [data]).fail(function(err, ev){
				alert("[Hotel Calendar]\nERROR: Can't update price!");
				$this.hcalendar.setDetailPrice(ev.detail.room_type, ev.detail.date, ev.detail.old_price);
			});
			
			console.log("NEW PRICE!");
			console.log(ev.detail.room_type);
			console.log(ev.detail.date);
			console.log(ev.detail.price);
			console.log(ev.detail.old_price);
		});
    },
    
    generate_hotel_calendar: function(){
    	var $this = this;
    	
    	/** DO MAGIC **/
    	var domains = this.generate_domains();
    	var full_domain = [false, domains['dates'][0], domains['dates'][1], domains['rooms'] || [], domains['reservations'] || []];
    	this._model.call('get_hcalendar_data', full_domain).then(function(results){
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
			}, results['pricelist']);
			
			var reservs = [];
			for (var r of results['reservations']) {
				var room = $this.hcalendar.getRoom(r[0]);
				var nreserv = new HReservation(
					r[1], // Id
					room, // Room
					r[2], // Title
					r[3], // Adults
					r[4], // Childrens
					moment.utc(r[5]).local(), // Date Start
					moment.utc(r[6]).local(), // Date End
					r[8] // Color
				);
				nreserv.addUserData({'reservation_line_id': r[7]});
				reservs.push(nreserv);
			}
			$this.hcalendar.setReservations(reservs);
		});
    },
    
    call_action: function(action) {
    	this.action_manager.do_action(action);
		$(document).find('.oe-control-panel').show();
    },
    
    get_pms_buttons_counts: function() {
    	this.$el.find('div.ninfo').hide();
    	
    	var domain = [];
    	var $badge = false;
    	
    	// Checkout Button
    	domain = [['checkout', '>=', moment().utc().startOf('day').format("YYYY-MM-DD HH:mm:ss")],
			['checkout','<=', moment().utc().endOf('day').format("YYYY-MM-DD HH:mm:ss")],
			['state','=','checkin']];

		var $badge_checkout = this.$el.find('#pms-menu #btn_action_checkout .badge');
		this._model.call('search_count', [domain]).then(function(count){
			if (count > 0) {
				$badge_checkout.text(count);
				$badge_checkout.parent().show();
			}
		});
    	
    	// Checkin Button
    	domain = [['checkin', '>=', moment().utc().startOf('day').format("YYYY-MM-DD HH:mm:ss")],
						['checkin','<=', moment().utc().endOf('day').format("YYYY-MM-DD HH:mm:ss")],
						['state','!=','checkin']];
    	
    	var $badge_checkin = this.$el.find('#pms-menu #btn_action_checkin .badge');
    	this._model.call('search_count', [domain]).then(function(count){
    		if (count > 0) {
    			$badge_checkin.text(count);
    			$badge_checkin.parent().show();
    		}
    	});
    	
    	// Charges Button
    	domain = [['invoice_status', 'in', ['to invoice', 'no']], ['reservation_id', '!=', false]];
    	
    	var $badge_charges = this.$el.find('#pms-menu #btn_action_paydue .badge');
    	new Model('hotel.folio').call('search_count', [domain]).then(function(count){
    		if (count > 0) {
    			$badge_charges.text(count);
    			$badge_charges.parent().show();
    		}
    	});
    },
    
    init_calendar_view: function(){
    	var $this = this;

		/** HACKISH ODOO VIEW **/
		$(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
		
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
			$this.on_change_filter_date(e);
	    });
		$dateTimePickerEnd.on("dp.change", function (e) {
			$this.on_change_filter_date(e);
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
		
        var date_begin = moment(new Date());
		var days = moment(date_begin).daysInMonth();
		var date_end = date_begin.clone().add(days, 'd');
		$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
		$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
		
		// View Events
		this.$el.find("#pms-search #search_query").on('change', function(ev){
			$this.reload_hcalendar_reservations();
		});
		this.$el.find("#pms-search #cal-pag-prev-plus").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(15, 'd');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(15, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-prev").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(1, 'd');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(1, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next-plus").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(15, 'd');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(15, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-next").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(1, 'd');
			var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(1, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		this.$el.find("#pms-search #cal-pag-selector").on('click', function(ev){
			// FIXME: Ugly repeated code. Change place.
			var $dateTimePickerBegin = $this.$el.find('#pms-search #date_begin');
			var $dateTimePickerEnd = $this.$el.find('#pms-search #date_end');
			var date_begin = moment();
			var days = moment(date_begin).daysInMonth();
			var date_end = date_begin.clone().add(days, 'd');
			$dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
			$dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
			
			ev.preventDefault();
		});
		
		/* BUTTONS */
		this.get_pms_buttons_counts();
		this.$el.find("#btn_action_checkout").on('click', function(ev){
			$this.call_action('alda_calendar.hotel_reservation_action_checkout');
		});
		this.$el.find("#btn_action_checkin").on('click', function(ev){
			$this.call_action('alda_calendar.hotel_reservation_action_checkin');
		});
		this.$el.find("#btn_action_paydue").on('click', function(ev){
			$this.call_action('alda_calendar.hotel_reservation_action_paydue');
		});
		this.$el.find("#btn_action_refresh").on('click', function(ev){
			window.location.reload();
		});
		
    	/** RENDER CALENDAR **/
		this.generate_hotel_calendar();
		
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
				$this.generate_hotel_calendar();
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
				$this.generate_hotel_calendar();
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
				$this.generate_hotel_calendar();
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
				$this.generate_hotel_calendar();
			});
		});
		
		return $.when();
    },
    
    on_change_filter_date: function(ev) {
    	var $dateTimePickerBegin = this.$el.find('#pms-search #date_begin');
		var $dateTimePickerEnd = this.$el.find('#pms-search #date_end');
		var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate();
		var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate();
    	if (date_begin && date_end && !date_begin.isSame(date_end) && this.hcalendar) {
    		this.hcalendar.setStartDate(date_begin, date_end.diff(date_begin,'days')+1);
    		this.reload_hcalendar_reservations();
    	}
    },
    
    reload_hcalendar_reservations: function() {
    	var $this = this;
    	var domains = this.generate_domains();
    	var full_domain = [false, domains['dates'][0], domains['dates'][1], domains['rooms'] || [], domains['reservations'] || [], false];
    	this._model.call('get_hcalendar_data', full_domain).then(function(results){
    		$this.reserv_tooltips = results['tooltips'];
    		var reservs = [];
			for (var r of results['reservations']) {
				var room = $this.hcalendar.getRoom(r[0]);
				var nreserv = new HReservation(
					r[1], // Id
					room, // Room
					r[2], // Title
					r[3], // Adults
					r[4], // Childrens
					moment.utc(r[5]).local(), // Date Start
					moment.utc(r[6]).local(), // Date End
					r[8] // Color
				);
				nreserv.addUserData({'reservation_line_id': r[7]});
				reservs.push(nreserv);
			}
			$this.hcalendar.pricelist = results['pricelist'];
			$this.hcalendar.setReservations(reservs);
		});
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

    	var date_begin = moment($dateTimePickerBegin.data("DateTimePicker").getDate().startOf('day')).utc().format("YYYY-MM-DD HH:mm:ss");
    	var date_end = moment($dateTimePickerEnd.data("DateTimePicker").getDate().startOf('day')).utc().format("YYYY-MM-DD HH:mm:ss");

    	
    	return {
    		'rooms': domainRooms,
    		'reservations': domainReservations,
    		'dates': [date_begin, date_end]
    	};
    }
});

core.view_registry.add('pms', HotelCalendarView);
return HotelCalendarView;

});



/*
self.action_manager.do_action({
        type: 'ir.actions.act_window',
        res_model: "quick.room.reservation",
        views: [[false, 'form']],
        target: 'new',
        context: {"room_id": $(this).attr("data"), 'date': $(this).attr("date")},
});
*/

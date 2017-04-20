odoo.define('alda_calendar.HotelCalendarView', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
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
    
    init_hotel_calendar: function(domain){
    	console.log("SS 22");
    	/*this._model.call('get_reservations_data', [domain]).then(function(results){
			console.log(results);
		});*/
    	
    	var options = {
			rooms: {
				Simple: {
					persons: 1,
					numbers: ['80','127','82','83']
				},
				Doble: {
					persons: 2,
					numbers: ['126','81','128','129','130']
				},
				Triple: {
					persons: 3,
					numbers: ['95','96','97']
				}
			},
			
			showPaginator: false,
		};
		var reservations = [
			{
				room_type: 'Doble',
				room_number: '128',
				room_beds: ['0','1'],
				start_date: '02/03/2017',
				end_date: '08/03/2017',
				title: 'Prueba #1',
				
			},
			{
				room_type: 'Doble',
				room_number: '126',
				room_beds: ['0','1'],
				start_date: '04/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #2',
				
			},
			{
				room_type: 'Doble',
				room_number: '127',
				room_beds: ['0','1'],
				start_date: '04/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #3',
				
			},
			{
				room_type: 'Doble',
				room_number: '129',
				room_beds: ['0','1'],
				start_date: '05/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #4',
				
			},
			{
				room_type: 'Doble',
				room_number: '130',
				room_beds: ['0','1'],
				start_date: '05/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #5',
				
			},
			{
				room_type: 'Simple',
				room_number: '81',
				room_beds: ['0'],
				start_date: '02/03/2017',
				end_date: '08/03/2017',
				title: 'Prueba #6',
				
			},
			{
				room_type: 'Simple',
				room_number: '82',
				room_beds: ['0'],
				start_date: '04/03/2017',
				end_date: '16/03/2017',
				title: 'Prueba #7',
				
			},
			{
				room_type: 'Simple',
				room_number: '80',
				room_beds: ['0'],
				start_date: '04/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #8',
				
			},
			{
				room_type: 'Simple',
				room_number: '83',
				room_beds: ['0'],
				start_date: '04/03/2017',
				end_date: '06/03/2017',
				title: 'Prueba #9',
				
			},
			{
				room_type: 'Triple',
				room_number: '95',
				room_beds: ['0','1','2'],
				start_date: '03/03/2017',
				end_date: '05/03/2017',
				title: 'Prueba #10',
				
			},
			{
				room_type: 'Triple',
				room_number: '96',
				room_beds: ['0','1','2'],
				start_date: '03/03/2017',
				end_date: '05/03/2017',
				title: 'Prueba #11',
				
			},
			{
				room_type: 'Triple',
				room_number: '97',
				room_beds: ['0','1','2'],
				start_date: '03/03/2017',
				end_date: '05/03/2017',
				title: 'Prueba #12',
				
			},
			{
				room_type: 'Simple',
				room_number: '83',
				room_beds: ['0'],
				start_date: '07/03/2017',
				end_date: '09/03/2017',
				title: 'Prueba #13',
				
			}
		];

		/** FIXME: HACKS **/
		$(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
		$(document).find('.oe-control-panel').remove(); // Remove "control panel" in the view
		
		/** VIEW SETTINGS **/
		// DATE TIME PICKERS
		var $this = this;
		var DTPickerOptions = { 
			'viewMode': 'months'
		};
		this.$el.find('#pms-search #date_begin').datetimepicker(DTPickerOptions);
		this.$el.find('#pms-search #date_end').datetimepicker($.extend({}, DTPickerOptions, { 'useCurrent': false }));
		this.$el.find("#pms-search #date_begin").on("dp.change", function (e) {
	        $this.$el.find('#pms-search #date_end').data("DateTimePicker").minDate(e.date);
	    });
		this.$el.find("#pms-search #date_end").on("dp.change", function (e) {
	        $this.$el.find('#pms-search #date_begin').data("DateTimePicker").maxDate(e.date);
	    });
		
		console.log("--- LLLLL ----");
		console.log(options);
		this.hcalendar = new HotelCalendarJS('#hcalendar', options, reservations, this.$el[0]);
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
		
		return $.when();
    }
});

core.view_registry.add('pms', HotelCalendarView);

});

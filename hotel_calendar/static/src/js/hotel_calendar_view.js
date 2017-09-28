/* global $, odoo, _, HotelCalendar, moment */
odoo.define('hotel_calendar.HotelCalendarView', function (require) {
"use strict";
/*
 * Hotel Calendar View
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */

var Core = require('web.core'),
    Bus = require('bus.bus').bus,
    //Data = require('web.data'),
    Time = require('web.time'),
    Model = require('web.DataModel'),
    View = require('web.View'),
    Common = require('web.form_common'),
    //Pyeval = require('web.pyeval'),
    ActionManager = require('web.ActionManager'),
    Utils = require('web.utils'),
    Dialog = require('web.Dialog'),
    Ajax = require('web.ajax'),
    ControlPanel = require('web.ControlPanel'),
    Session = require('web.session'),
    formats = require('web.formats'),

    _t = Core._t,
    _lt = Core._lt,
    QWeb = Core.qweb,
    l10n = _t.database.parameters,

    PUBLIC_PRICELIST_ID = 1, // Hard-Coded public pricelist id
    DEFAULT_ARRIVAL_HOUR = 14,
    DEFAULT_DEPARTURE_HOUR = 12,
    ODOO_DATE_MOMENT_FORMAT = 'YYYY-MM-DD',
    ODOO_DATETIME_MOMENT_FORMAT = ODOO_DATE_MOMENT_FORMAT + ' HH:mm:ss',
    L10N_DATE_MOMENT_FORMAT = "DD/MM/YYYY", //FIXME: Time.strftime_to_moment_format(l10n.date_format);
    L10N_DATETIME_MOMENT_FORMAT = L10N_DATE_MOMENT_FORMAT + ' ' + Time.strftime_to_moment_format(l10n.time_format);


/* HIDE CONTROL PANEL */
/* FIXME: Look's like a hackish solution */
ControlPanel.include({
  update: function(status, options) {
      if (typeof options.toHide === 'undefined')
          options.toHide = false;
      var action_stack = this.getParent().action_stack;
      if (action_stack && action_stack.length) {
          var active_action = action_stack[action_stack.length-1];
          if (active_action.widget && active_action.widget.active_view &&
                  active_action.widget.active_view.type === 'pms'){
              options.toHide = true;
          }
      }
      this._super(status, options);
      this._toggle_visibility(!options.toHide);
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
    _last_dates: [false, false],

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
        //var attrs = fv.arch.attrs,
        var self = this;

        var edit_check = new Model(this.dataset.model)
              .call("check_access_rights", ["write", false])
              .then(function (write_right) {
                self.write_right = write_right;
              }),
            init = new Model(this.dataset.model)
              .call("check_access_rights", ["create", false])
              .then(function (create_right) {
                self.create_right = create_right;
                self.init_calendar_view().then(function() {
                  //$(window).trigger('resize');
                  self.trigger('hotel_calendar_view_loaded', fv);
                  self.ready.resolve();
                });
              });
        this.fields_view = fv;
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
            var date_begin = ev.detail.newDate;
            var days = self._hcalendar.getOptions('days')-1;
            var date_end = date_begin.clone().add(days, 'd');

            var $dateTimePickerBegin = self.$el.find('#pms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#pms-search #date_end');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            self.reload_hcalendar_reservations(false, true);
        });
        this._hcalendar.addEventListener('hcalOnMouseEnterReservation', function(ev){
            var tp = self._reserv_tooltips[ev.detail.reservationObj.id];
            var arrival_hour = HotelCalendar.toMomentUTC(tp[2], ODOO_DATETIME_MOMENT_FORMAT).local().format('HH:mm'); // UTC to Local

            var qdict = {
                'name': tp[0],
                'phone': tp[1],
                'arrival_hour': arrival_hour
            };

            $(ev.detail.reservationDiv).tooltip({
                animation: true,
                html: true,
                placement: 'bottom',
                title: QWeb.render('HotelCalendar.TooltipReservation', qdict)
            }).tooltip('show');
        });
        this._hcalendar.addEventListener('hcalOnClickReservation', function(ev){
            var res_id = ev.detail.reservationObj.getUserData('folio_id');
            self._model.call('get_formview_id', [res_id, Session.user_context]).then(function(view_id){
                var pop = new Common.FormViewDialog(self, {
                    res_model: 'hotel.folio',
                    res_id: res_id,
                    title: _t("Open: ") + ev.detail.reservationObj.title,
                    view_id: view_id
                    //readonly: false
                }).open();
                pop.on('write_completed', self, function(){
                    self.trigger('changed_value');
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
                ncheckin: newReservation.startDate.clone().local().format(L10N_DATETIME_MOMENT_FORMAT),
                ncheckout: newReservation.endDate.clone().local().format(L10N_DATETIME_MOMENT_FORMAT),
                nroom: newReservation.room.number,
                ocheckin: oldReservation.startDate.clone().local().format(L10N_DATETIME_MOMENT_FORMAT),
                ocheckout: oldReservation.endDate.clone().local().format(L10N_DATETIME_MOMENT_FORMAT),
                oroom: oldReservation.room.number,
                hasReservesLinked: (linkedReservs && linkedReservs.length !== 0)?true:false
            };
            console.log(qdict);
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
                                'checkin': newReservation.startDate.format(ODOO_DATETIME_MOMENT_FORMAT),
                                'checkout': newReservation.endDate.format(ODOO_DATETIME_MOMENT_FORMAT),
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
        this._hcalendar.addEventListener('hcalOnUpdateSelection', function(ev){
        	for (var td of ev.detail.old_cells) {
        		$(td).tooltip('destroy');
        	}
        	if (ev.detail.cells.length > 1) {
	        	var last_cell = ev.detail.cells[ev.detail.cells.length-1];
	        	var date_cell_start = HotelCalendar.toMoment(self._hcalendar.etable.querySelector(`#${ev.detail.cells[0].dataset.hcalParentCell}`).dataset.hcalDate);
	        	var date_cell_end = HotelCalendar.toMoment(self._hcalendar.etable.querySelector(`#${last_cell.dataset.hcalParentCell}`).dataset.hcalDate);
	        	var nights = date_cell_end.diff(date_cell_start, 'days');
	        	var qdict = {
	        		'total_price': Number(ev.detail.totalPrice).toLocaleString(),
	        		'nights': nights
	        	};
	        	$(last_cell).tooltip({
	                animation: false,
	                html: true,
	                placement: 'top',
	                title: QWeb.render('HotelCalendar.TooltipSelection', qdict)
	            }).tooltip('show');
        	}
        });
        this._hcalendar.addEventListener('hcalOnChangeSelection', function(ev){
            var parentRow = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentRow}`);
            var parentCellStart = document.querySelector(`#${ev.detail.cellStart.dataset.hcalParentCell}`);
            var parentCellEnd = document.querySelector(`#${ev.detail.cellEnd.dataset.hcalParentCell}`);
            var startDate = HotelCalendar.toMoment(parentCellStart.dataset.hcalDate);
            var endDate = HotelCalendar.toMoment(parentCellEnd.dataset.hcalDate);
            var room = self._hcalendar.getRoom(parentRow.dataset.hcalRoomObjId);
            var numBeds = room.shared?(ev.detail.cellEnd.dataset.hcalBedNum - ev.detail.cellStart.dataset.hcalBedNum)+1:room.capacity;
            var HotelFolioObj = new Model('hotel.folio');

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

            startDate.set({'hour': DEFAULT_ARRIVAL_HOUR, 'minute': 0, 'second': 0});
            endDate.set({'hour': DEFAULT_DEPARTURE_HOUR, 'minute': 0, 'second': 0});

            // Creater/Select Partner + Create Folio + Create Reservation + Confirm Folio? = Fucking Crazy uH :/
            var pop = new Common.SelectCreateDialog(self, {
                res_model: 'res.partner',
                domain: [],
                title: _t("Select Partner"),
                disable_multiple_selection: true,
                on_selected: function(element_ids) {
                	var partner_id = element_ids[0];
                	// Create Folio
                	var data = {
                		'partner_id': partner_id,
                	};
                	HotelFolioObj.call('create', [data]).then(function(result){
                        var folio_id = result;
                        // Get Unit Price of Virtual Room
                        var popCreate = new Common.FormViewDialog(self, {
                            res_model: 'hotel.reservation',
                            context: {
                            	//'default_partner_id': partner_id,
                            	'default_folio_id': folio_id,
                                'default_checkin': startDate.utc().format(ODOO_DATETIME_MOMENT_FORMAT),
                                'default_checkout': endDate.utc().format(ODOO_DATETIME_MOMENT_FORMAT),
                                'default_adults': numBeds,
                                'default_children': 0,
                                'default_order_id.parter_id': partner_id,
                                'default_product_id': room.id,
                                //'default_product_uom': room.getUserData('uom_id'),
                                //'default_product_uom_qty': 1,
                                //'default_state': 'draft',
//                                          //'product_uos': 1,
                                'default_name': `${room.number}`,
                                //'default_reservation_lines': reservation_lines,
                                //'default_price_unit': result['total_price']
                            },
                            title: _t("Create: ") + _t("Reservation"),
                            initial_view: "form",
                            disable_multiple_selection: true,
                            form_view_options: { 'not_interactible_on_create':true },
                            create_function: function(data, options) {
                            	var dself = this;
                                var def = $.Deferred();
                                var res_id = true;
                                var dataset = self.dataset;
                                options = options || {};
                                var internal_options = _.extend({}, options, {'internal_dataset_changed': true});
                                self.mutex.exec(function(){
                                	// FIXME: Workaround to get values of 'only-read' fields...
                                	data = _.extend(data, {
                                		'folio_id': folio_id,
                                		'name': `${room.number}`,
                                	});
                                    return dataset.create(data, internal_options).then(function (id) {
                                        dataset.ids.push(id);
                                        res_id = id;
                                        dself._record_created = true;
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
                                                disabled: res_id < 0,
                                                click: function () {
                                                	HotelFolioObj.call('action_confirm', [folio_id]).then(function(results){
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
                                        def.resolve(res_id);
                                    });
                                });

                                return def;
                            },
                            read_function: function(ids, fields, options) {
                                return self.dataset.read_ids(ids, fields, options);
                            }
                        }).open();
                        popCreate.view_form.on('on_button_cancel', popCreate, function(){
                        	HotelFolioObj.call('unlink', [[folio_id]]).fail(function(){

                        	});
                        });
                        popCreate.on('closed', popCreate, function(){
                        	if (!this.dataset.ids.length) {
                        		HotelFolioObj.call('unlink', [[folio_id]]).fail(function(){

                            	});
                        	}
                        });
                    });
                }
            }).open();
        });

        this._hcalendar.addEventListener('hcalOnChangeRoomTypePrice', function(ev){
            var qdict = {
                'date':  ev.detail.date.clone().local().format(L10N_DATE_MOMENT_FORMAT),
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
        var oparams = [
          false,
          domains['dates'][0].format(ODOO_DATETIME_MOMENT_FORMAT),
          domains['dates'][1].format(ODOO_DATETIME_MOMENT_FORMAT),
          domains['rooms'] || [],
          domains['reservations'] || []
        ];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            self._reserv_tooltips = results['tooltips'];
            var rooms = [];
            for (var r of results['rooms']) {
                var nroom = new HRoom(
                    r[0], // Id
                    r[1], // Name
                    r[2], // Capacity
                    r[4], // Category
                    r[5], // Shared Room
                    r[7]  // Price
                );
                nroom.addUserData({
                    'categ_id': r[3],
                    'uom_id': r[6],
                    'price_from': r[8],
                    'inside_rooms': r[9]
                });
                rooms.push(nroom);
            }
            console.log(domains['dates']);
            self.create_calendar({
                startDate: HotelCalendar.toMomentUTC(domains['dates'][0], ODOO_DATETIME_MOMENT_FORMAT),
                rooms: rooms,
                showPaginator: false
            }, results['pricelist']);

            var reservs = [];
            for (var r of results['reservations']) {
            	console.log("===BBBB");
            	console.log(HotelCalendar.toMomentUTC(r[5], ODOO_DATETIME_MOMENT_FORMAT));
                var room = self._hcalendar.getRoom(r[0]);
                var nreserv = new HReservation(
                    r[1], // Id
                    room, // Room
                    r[2], // Title
                    r[3], // Adults
                    r[4], // Childrens
                    HotelCalendar.toMomentUTC(r[5], ODOO_DATETIME_MOMENT_FORMAT), // Date Start
                    HotelCalendar.toMomentUTC(r[6], ODOO_DATETIME_MOMENT_FORMAT), // Date End
                    r[8], // Color
                    r[9] || false, // Read Only
                    r[10] || false, // Move Days
                    r[11] || false // Move Rooms
                );
                nreserv.addUserData({'folio_id': r[7]});
                reservs.push(nreserv);
            }
            self._hcalendar.setReservations(reservs);
            self.assign_extra_info_();
        });
    },

    assign_extra_info_: function() {
    	var self = this;
        $(this._hcalendar.etable).find('.hcal-cell-room-type-group-item.btn-hcal-3d').on("mouseenter", function(){
        	var $this = $(this);
        	var room = self._hcalendar.getRoom($this.parent().data("hcalRoomObjId"));
        	var qdict = {
    			'price_from': room.getUserData('price_from'),
                'inside_rooms': room.getUserData('inside_rooms'),
                'num_inside_rooms': room.getUserData('inside_rooms').length,
                'name': room.number
        	};
        	$this.tooltip({
                animation: true,
                html: true,
                placement: 'right',
                title: QWeb.render('HotelCalendar.TooltipRoom', qdict)
            }).tooltip('show');
        });
    },

    call_action: function(action) {
        this._action_manager.do_action(action);
    },

    update_buttons_counter: function() {
        var self = this;
        var domain = [];

        var HotelFolioObj = new Model('hotel.folio');

         // Checkouts Button
        domain = [['checkouts_reservations', '>', 0]];
        HotelFolioObj.call('search_count', [domain]).then(function(count){
            var $ninfo = self.$el.find('#pms-menu #btn_action_checkout div.ninfo');
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
        domain = [['checkins_reservations', '>', 0]];
        HotelFolioObj.call('search_count', [domain]).then(function(count){
            var $ninfo = self.$el.find('#pms-menu #btn_action_checkin div.ninfo');
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
        domain = [['invoices_amount','>',0 ],['room_lines.checkout','<=', moment().startOf('day').utc().format(ODOO_DATETIME_MOMENT_FORMAT)]];
        HotelFolioObj.call('search_count', [domain]).then(function(count){
        	var $ninfo = self.$el.find('#pms-menu #btn_action_paydue div.ninfo');
        	var $badge_charges = self.$el.find('#pms-menu #btn_action_paydue .badge');
        	if (count > 0) {
        		$badge_charges.text(count);
        		$badge_charges.parent().show();
        		$ninfo.show();
            } else {
            	$ninfo.hide();
            }
       });
    },

    init_calendar_view: function(){
        var self = this;

        /** HACKISH ODOO VIEW **/
        //this._action_manager.main_control_panel.$el.hide();
        $(document).find('.oe-view-manager-view-pms').css('overflow', 'initial'); // No Scroll here!
        //this.$el.parent().parent().css('overflow', 'none');

        /** VIEW CONTROLS INITIALIZATION **/
        // DATE TIME PICKERS
        var l10nn = _t.database.parameters
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
        //  'useCurrent': true,
        //}));

        //var $dateTimePickerSelector = this.$el.find('#pms-search #cal-pag-selector-calendar');
        //$dateTimePickerSelector.datetimepicker($.extend({}, DTPickerOptions, {'inline':true, 'sideBySide': false}));
        //$dateTimePickerSelector.on("dp.change", function (e) {
        //  console.log(e);
            /*var date_begin = moment(this.data("DateTimePicker").getDate());
            var days = moment(date_begin).daysInMonth();
            var date_end = date_begin.clone().add(days, 'd');
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);*/
        //});

        var date_begin = moment().startOf('day');
        var days = date_begin.daysInMonth();
        var date_end = date_begin.clone().add(days, 'd').endOf('day');
        $dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
        $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
        this._last_dates = this.generate_domains()['dates'];

        // View Events
        this.$el.find("#pms-search #search_query").on('change', function(ev){
            self.reload_hcalendar_reservations(true, false);
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
            var date_begin = moment().startOf('day').utc();
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
//        this.$el.find("#btn_action_refresh").on('click', function(ev){
//            window.location.reload();
//        });

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
        var hardmode = isStartDate || date_begin.isAfter(date_end);
        if (date_begin && date_end && this._hcalendar) {
            var days = hardmode?date_begin.daysInMonth():date_end.diff(date_begin,'days');
            if (hardmode) {
                var ndate_end = date_begin.clone().add(days, 'd');
                $dateTimePickerEnd.data("ignore_onchange", true);
                $dateTimePickerEnd.data("DateTimePicker").setDate(ndate_end);
            }
            this._hcalendar.setStartDate(date_begin, days);
            this.reload_hcalendar_reservations(false, true);
        }
    },

    _on_bus_signal: function(notifications) {
        var need_reload_pricelists = false;
        for (var notif of notifications) {
          if (notif[0][1] === 'hotel.reservation') {
            switch (notif[1]['type']) {
              case 'reservation':
                var reserv = notif[1]['reservation'];
                // Only show notifications of other users
                if (notif[1]['userid'] != this.dataset.context.uid) {
                  var qdict = reserv;
                  qdict = _.extend(qdict, {
                    'checkin': HotelCalendar.toMomentUTC(qdict['checkin'], ODOO_DATETIME_MOMENT_FORMAT).local().format(L10N_DATETIME_MOMENT_FORMAT), // UTC -> Local
                    'checkout': HotelCalendar.toMomentUTC(qdict['checkout'], ODOO_DATETIME_MOMENT_FORMAT).local().format(L10N_DATETIME_MOMENT_FORMAT), // UTC -> Local
                    'username': notif[1]['username'],
                    'userid': notif[1]['userid']
                  });
                  var msg = QWeb.render('HotelCalendar.Notification', qdict);
                  if (notif[1]['subtype'] === "notify") {
                      this.do_notify(notif[1]['title'], msg, true);
                  } else if (notif[1]['subtype'] === "warn") {
                      this.do_warn(notif[1]['title'], msg, true);
                  }
                }

                // Create/Update/Delete reservation
                if (notif[1]['action'] === 'unlink' || reserv['state'] === 'cancelled') {
                  this._hcalendar.removeReservation(reserv['reserv_id']);
                  this._reserv_tooltips = _.pick(this._reserv_tooltips, function(value, key, obj){ return key != reserv['reserv_id']; });
                } else {
                  var room = this._hcalendar.getRoom(reserv['product_id']);
                  if (room) {
                    var nreserv = new HReservation(
                      reserv['reserv_id'],
                      room,
                      reserv['partner_name'],
                      reserv['adults'],
                      reserv['children'],
                      HotelCalendar.toMomentUTC(reserv['checkin'], ODOO_DATETIME_MOMENT_FORMAT),
                      HotelCalendar.toMomentUTC(reserv['checkout'], ODOO_DATETIME_MOMENT_FORMAT),
                      reserv['reserve_color'],
                      reserv['read_only'],
                      reserv['fix_days'],
                      reserv['fix_rooms']
                    );
                    nreserv.addUserData({'folio_id': reserv['folio_id']});
                    this._reserv_tooltips[reserv['reserv_id']] = notif[1]['tooltip'];
                    this._hcalendar.addReservations([nreserv]);
                  }
                }
                break;
              case 'pricelist':
                var price = notif[1]['price'];
                this._hcalendar.addPricelist(price);
                break;
              default:
                // Do Nothing
            }
          }
        }
    },

    reload_hcalendar_reservations: function(clearReservations, withPricelist) {
        var self = this;
        var domains = this.generate_domains();
        // Clip dates
        var dfrom = domains['dates'][0],
            dto = domains['dates'][1];
        if (dfrom.isBetween(this._last_dates[0], this._last_dates[1], 'days') && dto.isAfter(this._last_dates[1], 'day')) {
          dfrom = this._last_dates[1];
        } else if (this._last_dates[0].isBetween(dfrom, dto, 'days') && this._last_dates[1].isAfter(dfrom, 'day')) {
          dto = this._last_dates[0];
        } else {
          clearReservations = true;
        }

        dfrom = dfrom.local().startOf('day').utc();
        dto = dto.local().endOf('day').utc();

        var oparams = [
          false,
          dfrom.format(ODOO_DATETIME_MOMENT_FORMAT),
          dto.format(ODOO_DATETIME_MOMENT_FORMAT),
          domains['rooms'] || [],
          domains['reservations'] || [],
          false,
          withPricelist || false
        ];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            self._reserv_tooltips = _.extend(self._reserv_tooltips, results['tooltips']);
            var reservs = [];
            for (var r of results['reservations']) {
                var room = self._hcalendar.getRoom(r[0]);
                var nreserv = new HReservation(
                    r[1], // Id
                    room, // Room
                    r[2], // Title
                    r[3], // Adults
                    r[4], // Childrens
                    HotelCalendar.toMomentUTC(r[5], ODOO_DATETIME_MOMENT_FORMAT), // Date Start
                    HotelCalendar.toMomentUTC(r[6], ODOO_DATETIME_MOMENT_FORMAT), // Date End
                    r[8], // Color
                    r[9] || false, // Read Only
                    r[10] || false, // Move Days
                    r[11] || false // Move Rooms
                );
                nreserv.addUserData({'folio_id': r[7]});
                reservs.push(nreserv);
            }

            if (withPricelist) {
              self._hcalendar.addPricelist(results['pricelist']);
            }
            if (clearReservations) {
              self._hcalendar.setReservations(reservs);
            } else {
              self._hcalendar.addReservations(reservs);
            }

            self.assign_extra_info_();
        });
        this._last_dates = domains['dates'];
        this.update_buttons_counter();
    },

    generate_domains: function() {
        var domainRooms = [];
        var category = this.$el.find('#pms-search #type_list').val();
        if (category) { domainRooms.push(['categ_id.id', 'in', category]); }
        var floor = this.$el.find('#pms-search #floor_list').val();
        if (floor) { domainRooms.push(['floor_id.id', 'in', floor]); }
        var amenities = this.$el.find('#pms-search #amenities_list').val();
        if (amenities) {
        	for (var amenity of amenities) {
        		domainRooms.push(['room_amenities.id', '=', amenity]);
        	}
        }
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

        var date_begin = moment($dateTimePickerBegin.data("DateTimePicker").getDate()).startOf('day').utc();
        var date_end = moment($dateTimePickerEnd.data("DateTimePicker").getDate()).endOf('day').utc();
        
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

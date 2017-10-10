/* global $, odoo, _, HotelCalendarManagement, moment */
odoo.define('hotel_calendar.HotelCalendarManagementView', function (require) {
"use strict";
/*
 * Hotel Calendar Management View
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

    CALENDAR_DAYS = 5,
    ODOO_DATETIME_MOMENT_FORMAT = "YYYY-MM-DD HH:mm:ss",
    ODOO_DATE_MOMENT_FORMAT = "YYYY-MM-DD",
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
                    active_action.widget.active_view.type === 'mpms'){
                options.toHide = true;
            }
        }
        this._super(status, options);
        this._toggle_visibility(!options.toHide);
    }
});

var HotelCalendarManagementView = View.extend({
    /** VIEW OPTIONS **/
    template: "hotel_calendar.HotelCalendarManagementView",
    display_name: _lt('Hotel Calendar Management'),
    icon: 'fa fa-map-marker',
    view_type: "mpms",
    searchable: false,
    searchview_hidden: true,

    // Custom Options
    _model: null,
    _hcalendar: null,
    _action_manager: null,
    _last_dates: [false, false],
    _pricelist_id: null,
    _restriction_id: null,

    /** VIEW METHODS **/
    init: function(parent, dataset, view_id, options) {
        this._super(parent);
        this.ready = $.Deferred();
        this.set_default_options(options);
        this.dataset = dataset;
        this.model = dataset.model;
        this.fields_view = {};
        this.view_id = view_id;
        this.view_type = 'mpms';
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
                  self.trigger('hotel_calendar_management_view_loaded', fv);
                  self.ready.resolve();
                });
              });
        this.fields_view = fv;
        return $.when(edit_check, init);
    },

    do_show: function() {
        var $widget = this.$el.find("#hcal_management_widget");
        if ($widget) {
            $widget.show();
        }
        this.do_push_state({});
        return this._super();
    },
    do_hide: function () {
        var $widget = this.$el.find("#hcal_management_widget");
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
    save_changes: function() {
        var btn_save = this.$el.find('#btn_save_changes');
        if (!btn_save.hasClass('need-save')) {
            return;
        }
        btn_save.removeClass('need-save');

        var pricelist = this._hcalendar.getPricelist(true);
        var restrictions = this._hcalendar.getRestrictions(true);
        var availability = this._hcalendar.getAvailability(true);
        console.log("======== DATA");
        console.log(pricelist);
        console.log(restrictions);
        console.log(availability);

        var params = this.generate_params();
        var oparams = [false, params['prices'], params['restrictions'], pricelist, restrictions, availability];
        this._model.call('save_changes', oparams).then(function(results){
            console.log("== SAVE RESULTS");
            console.log(results);
        });
    },

    create_calendar: function(options) {
        var self = this;
        // CALENDAR
        if (this._hcalendar) {
            delete this._hcalendar;
        }
        var $widget = this.$el.find("#hcal_management_widget");
        var $hcal = $widget.find('#hcalendar_management');
        if ($hcal) { $hcal.remove(); }
        $widget.append("<div id='hcalendar_management'></div>");

        this._hcalendar = new HotelCalendarManagement('#hcalendar_management', options, this.$el[0]);
        this._hcalendar.addEventListener('hcOnChangeDate', function(ev){
            var date_begin = moment(ev.detail.newDate);
            var days = self._hcalendar.getOptions('days')-1;
            var date_end = date_begin.clone().add(days, 'd');

            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            self.reload_hcalendar_management();
        });
        this._hcalendar.addEventListener('hcmOnInputChanged', function(ev){
            var btn_save = self.$el.find('#btn_save_changes');
            btn_save.addClass('need-save');
            console.log(ev.detail);
        });
    },

    generate_hotel_calendar: function(){
        var self = this;

        /** DO MAGIC **/
        var params = this.generate_params();
        var oparams = [false, params['dates'][0], params['dates'][1], false, false, true];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            var rooms = [];
            for (var r of results['rooms']) {
                var nroom = new HVRoom(
                    r[0], // Id
                    r[1], // Name
                    r[2], // Capacity
                    r[3], // Price
                );
                rooms.push(nroom);
            }

            // Get Pricelists
            self._pricelist_id = results['pricelist_id'];
            new Model('product.pricelist').query(['id','name']).all().then(function(resultsPricelist){
                var $list = self.$el.find('#mpms-search #price_list');
                $list.html('');
                resultsPricelist.forEach(function(item, index){
                    $list.append(`<option value="${item.id}" ${item.id==self._pricelist_id?'selected':''}>${item.name}</option>`);
                });
                $list.select2();
                $list.on('change', function(ev){
                    self._check_unsaved_changes(function(){
                        self.reload_hcalendar_management();
                    });
                });
            });

            // Get Restrictions
            self._restriction_id = results['restriction_id'];
            new Model('hotel.virtual.room.restriction').query(['id','name']).all().then(function(resultsRestrictions){
                var $list = self.$el.find('#mpms-search #restriction_list');
                $list.html('');
                resultsRestrictions.forEach(function(item, index){
                    $list.append(`<option value="${item.id}">${item.name}</option>`);
                });
                $list.select2();
                $list.on('change', function(ev){
                    self._check_unsaved_changes(function(){
                        self.reload_hcalendar_management();
                    });
                });
            });

            self.create_calendar({
                rooms: rooms,
                days: CALENDAR_DAYS,
                dateFormatLong: ODOO_DATETIME_MOMENT_FORMAT,
                dateFormatShort: ODOO_DATE_MOMENT_FORMAT
            });
            self._hcalendar.setData(results['prices'], results['restrictions'], results['availability']);
        });
    },

    call_action: function(action) {
        this._action_manager.do_action(action);
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
        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');
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
        //this.$el.find('#mpms-search #cal-pag-selector').datetimepicker($.extend({}, DTPickerOptions, {
        //  'useCurrent': true,
        //}));

        //var $dateTimePickerSelector = this.$el.find('#mpms-search #cal-pag-selector-calendar');
        //$dateTimePickerSelector.datetimepicker($.extend({}, DTPickerOptions, {'inline':true, 'sideBySide': false}));
        //$dateTimePickerSelector.on("dp.change", function (e) {
        //  console.log(e);
            /*var date_begin = moment(this.data("DateTimePicker").getDate());
            var days = moment(date_begin).daysInMonth();
            var date_end = date_begin.clone().add(days, 'd');
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);*/
        //});

        var date_begin = moment().utc().startOf('day');
        var date_end = date_begin.clone().add(CALENDAR_DAYS, 'd').endOf('day');
        $dateTimePickerBegin.data("ignore_onchange", true);
        $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
        $dateTimePickerEnd.data("ignore_onchange", true);
        $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);
        this._last_dates = [date_begin.utc().format(ODOO_DATETIME_MOMENT_FORMAT),
                            date_end.utc().format(ODOO_DATETIME_MOMENT_FORMAT)];

        // View Events
        this.$el.find("#mpms-search #cal-pag-prev-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(15, 'd').startOf('day');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(15, 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-prev").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().subtract(1, 'd').startOf('day');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().subtract(1, 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next-plus").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(15, 'd').startOf('day');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(15, 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-next").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = $dateTimePickerBegin.data("DateTimePicker").getDate().add(1, 'd').startOf('day');
            var date_end = $dateTimePickerEnd.data("DateTimePicker").getDate().add(1, 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });
        this.$el.find("#mpms-search #cal-pag-selector").on('click', function(ev){
            // FIXME: Ugly repeated code. Change place.
            var $dateTimePickerBegin = self.$el.find('#mpms-search #date_begin');
            var $dateTimePickerEnd = self.$el.find('#mpms-search #date_end');
            var date_begin = moment().utc().startOf('day');
            var date_end = date_begin.clone().add(self._hcalendar.getOptions('days'), 'd').endOf('day');
            $dateTimePickerBegin.data("ignore_onchange", true);
            $dateTimePickerBegin.data("DateTimePicker").setDate(date_begin);
            $dateTimePickerEnd.data("DateTimePicker").setDate(date_end);

            ev.preventDefault();
        });

        // Save Button
        this.$el.find("#btn_save_changes").on('click', function(ev){
            self.save_changes();
        });

        /** RENDER CALENDAR **/
        this.generate_hotel_calendar();

        return $.when();
    },

    on_change_filter_date: function(ev, isStartDate) {
        var self = this;
        isStartDate = isStartDate || false;
        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');

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
            var days = hardmode?this._hcalendar.getOptions('days'):date_end.diff(date_begin,'days');
            if (hardmode) {
                var ndate_end = date_begin.clone().add(days, 'd');
                $dateTimePickerEnd.data("ignore_onchange", true);
                $dateTimePickerEnd.data("DateTimePicker").setDate(ndate_end);
            }

            this._check_unsaved_changes(function(){
                self._hcalendar.setStartDate(date_begin, days);
                self.reload_hcalendar_management();
            });
        }
    },

    _on_bus_signal: function(notifications) {

    },

    reload_hcalendar_management: function() {
        var self = this;
        var params = this.generate_params();
        var oparams = [false, params['dates'][0], params['dates'][1], params['prices'], params['restrictions'], false];
        this._model.call('get_hcalendar_all_data', oparams).then(function(results){
            self._hcalendar.setData(results['prices'], results['restrictions'], results['availability']);
        });
        this._last_dates = params['dates'];
    },

    generate_params: function() {
        var fullDomain = [];
        var prices = this.$el.find('#mpms-search #price_list').val();
        var restrictions = this.$el.find('#mpms-search #restriction_list').val();

        var $dateTimePickerBegin = this.$el.find('#mpms-search #date_begin');
        var $dateTimePickerEnd = this.$el.find('#mpms-search #date_end');

        var date_begin = moment($dateTimePickerBegin.data("DateTimePicker").getDate()).startOf('day').utc().format(ODOO_DATE_MOMENT_FORMAT);
        var date_end = moment($dateTimePickerEnd.data("DateTimePicker").getDate()).endOf('day').utc().format(ODOO_DATE_MOMENT_FORMAT);

        return {
            'dates': [date_begin, date_end],
            'prices': prices,
            'restrictions': restrictions
        };
    },

    _check_unsaved_changes: function(fnCallback) {
        var self = this;
        var btn_save = this.$el.find("#btn_save_changes");
        if (!btn_save.hasClass('need-save')) {
            btn_save.removeClass('need-save');
            fnCallback();
            return;
        }

        new Dialog(self, {
            title: _t("Unsaved Changes!"),
            buttons: [
                {
                    text: _t("Yes, save it"),
                    classes: 'btn-primary',
                    close: true,
                    click: function() {
                        self.save_changes();
                        fnCallback();
                    }
                },
                {
                    text: _t("No"),
                    close: true,
                    click: function() {
                        btn_save.removeClass('need-save');
                        fnCallback();
                    }
                }
            ],
            $content: QWeb.render('HotelCalendarManagement.UnsavedChanges', {})
        }).open();
    }
});

Core.view_registry.add('mpms', HotelCalendarManagementView);
return HotelCalendarManagementView;

});

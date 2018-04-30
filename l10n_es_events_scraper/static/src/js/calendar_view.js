odoo.define('l10n_es_events_scraper.CalendarView', function (require) {
  'use strict';

  var CalendarView = require('web_calendar.CalendarView');
  var ActionManager = require('web.ActionManager');

  var EventScraperCalendarView = CalendarView.include({
    _action_manager: null,

    init: function(parent, dataset, fields_view, options) {
      this._super.apply(this, arguments);
      this._action_manager = this.findAncestor(function(ancestor){ return ancestor instanceof ActionManager; });
    },

    render_buttons: function($node) {
      var self = this;
      this._super($node);
      this.$buttons.on('click', 'button.o_calendar_button_import_events', function () {
          self._action_manager.do_action('l10n_es_events_scraper.action_import_city_events');
      });
    }
  });

  return EventScraperCalendarView;
});

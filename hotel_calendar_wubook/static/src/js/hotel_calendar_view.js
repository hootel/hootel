/* global odoo, $ */
odoo.define('hotel_calendar_wubook.HotelCalendarViewWuBook', function (require) {
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
  var QWeb = Core.qweb;

  var _wubookNotifReservationsDomain = [
    ['wrid', '!=', 'none'],
    '|', ['to_assign', '=', true], ['to_read', '=', true]
  ];
  var _wubookIssuesDomain = [
    ['to_read', '=', true]
  ];

  var HotelCalendarViewWuBook = HotelCalendarView.include({
    update_buttons_counter: function () {
      this._super();
      var self = this;

      // Cloud Reservations
      new Model('hotel.reservation').call('search_count', [_wubookNotifReservationsDomain]).then(function (count) {
        var $button = self.$el.find('#btn_channel_manager_request');
        var $text = self.$el.find('#btn_channel_manager_request .cloud-text');
        if (count > 0) {
          $button.addClass('incoming');
          $text.text(count);
          $text.show();
        } else {
          $button.removeClass('incoming');
          $text.hide();
        }
      });

      // Issues
      new Model('wubook.issue').call('search_count', [_wubookIssuesDomain]).then(function (count) {
        var $ninfo = self.$el.find('#pms-menu #btn_action_issues div.ninfo');
        var $badgeIssues = $ninfo.find('.badge');
        if (count > 0) {
          $badgeIssues.text(count);
          $badgeIssues.parent().show();
          $ninfo.show();
        } else {
          $ninfo.hide();
        }
      });
    },

    init_calendar_view: function () {
      var self = this;
      return $.when(this._super()).then(function () {
        var deferredPromises = [];
        self.$el.find('#btn_channel_manager_request').on('click', function (ev) {
          new Common.SelectCreateDialog(self, {
            res_model: 'hotel.reservation',
            domain: _wubookNotifReservationsDomain,
            title: _t('WuBook Reservations to Assign'),
            disable_multiple_selection: true,
            no_create: true,
            on_selected: function (elementIds) {
              return self._model.call('get_formview_id', [elementIds[0], Session.user_context]).then(function (viewId) {
                var popView = new Common.FormViewDialog(self, {
                  res_model: 'hotel.reservation',
                  res_id: elementIds[0],
                  title: _t('Open: ') + _t('Reservation'),
                  view_id: viewId
                }).open();
                popView.on('write_completed', self, function () {
                  self.trigger('changed_value');
                });
                popView.on('closed', self, function () {
                  self.reload_hcalendar_reservations(); // Here because don't trigger 'write_completed' when change state to confirm
                });
              });
            }
          }).open();
        });

        self.$el.find('#btn_action_issues').on('click', function (ev) {
          self.call_action('hotel_calendar_wubook.calendar_wubook_issues_action');
        });

        return $.when.apply($, deferredPromises);
      });
    },

    _on_bus_signal: function (notifications) {
      this._super(notifications);
      for (var notif of notifications) {
        if (notif[1]['userid'] === this.dataset.context.uid) {
          continue;
        }
        if (notif[0][1] === 'hotel.reservation') {
          if (notif[1]['type'] === 'issue') {
            var issue = notif[1]['issue'];
            var qdict = issue;
            var msg = QWeb.render('HotelCalendarWuBook.NotificationIssue', qdict);
            if (notif[1]['subtype'] === 'notify') {
              this.do_notify(notif[1]['title'], msg, true);
            } else if (notif[1]['subtype'] === 'warn') {
              this.do_warn(notif[1]['title'], msg, true);
            }
          }
        }
      }
    },

    _generate_reservation_tooltip_dict: function(tp) {
      var qdict = this._super(tp);
      qdict['channel_name'] = tp[5];
      return qdict;
    },
  });

  return HotelCalendarViewWuBook;
});

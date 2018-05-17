/* global odoo, $ */
odoo.define('report_qweb_pdf_preview.report', function (require) {
  'use strict';
  /*
   * Report QWeb PDF Preview
   * GNU Public License
   * Alexandre Díaz <dev@redneboa.es>
   */

  var ActionManager = require('web.ActionManager');
  var Dialog = require('web.Dialog');
  var Core = require('web.core');
  var Session = require('web.session');

  var _t = Core._t;
  var QWeb = Core.qweb;

  // FIXME: Function copied from Odoo JS
  var make_report_url = function (action) {
      var report_urls = {
          'qweb-html': '/report/html/' + action.report_name,
          'qweb-pdf': '/report/pdf/' + action.report_name,
          'controller': action.report_file,
      };
      if (_.isUndefined(action.data) || _.isNull(action.data) || (_.isObject(action.data) && _.isEmpty(action.data))) {
          if (action.context.active_ids) {
              var active_ids_path = '/' + action.context.active_ids.join(',');
              report_urls = _.mapObject(report_urls, function (value, key) {
                  return value += active_ids_path;
              });
          }
      } else {
          var serialized_options_path = '?options=' + encodeURIComponent(JSON.stringify(action.data));
          serialized_options_path += '&context=' + encodeURIComponent(JSON.stringify(action.context));
          report_urls = _.mapObject(report_urls, function (value, key) {
              return value += serialized_options_path;
          });
      }
      return report_urls;
  };

  ActionManager.include({

    ir_actions_report_xml: function (action, options) {
      var self = this;
      action = _.clone(action);

      if (action.report_type === 'qweb-pdf-preview') {
        var report_urls = make_report_url(action);
        Session.rpc('/report/check_wkhtmltopdf').then(function (state) {
          if (state === 'upgrade' || state === 'ok') {
            var response = [
              report_urls['qweb-pdf'],
              'qweb-pdf'
            ];

            self.ir_actions_act_window_close(action, options);
            self._open_viewer(encodeURIComponent(`/report/download?token=123&data=${encodeURIComponent(JSON.stringify(response))}`));
          } else {
            this._super(action, options);
          }
        });
      }
    },

    _open_viewer: function(url) {
      var qdict = { filepath: url };
      var dialog = new Dialog(this, {
          title: _t("PDF Viewer"),
          buttons: [
            {
              text: _t("Close"),
              classes: 'btn-primary',
              close: true,
            }
          ],
          $content: QWeb.render('report_qweb_pdf_preview.ViewerDialog', qdict)
      }).open();
    }

  });

});

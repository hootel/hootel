/* global odoo, $ */
odoo.define('report_qweb_pdf_print.report', function (require) {
  'use strict';
  /*
   * Report QWeb PDF Print
   * GNU Public License
   * Alexandre Díaz <dev@redneboa.es>
   */

  var ActionManager = require('web.ActionManager');
  var Core = require('web.core');
  var Session = require('web.session');

  var _t = Core._t;
  var QWeb = Core.qweb;

  ActionManager.include({

    ir_actions_report_xml: function (action, options) {
      var self = this;
      action = _.clone(action);

      if (action.report_type === 'qweb-pdf-print') {
        Session.rpc('/report/check_wkhtmltopdf').then(function (state) {
          if (state === 'upgrade' || state === 'ok') {
            // Trigger the download of the PDF report.
            var response = [
              '/report/pdf/' + action.report_name,
              'qweb-pdf'
            ];

            console.log(JSON.stringify(response));
            self.ir_actions_act_window_close(action, options);

            // session.get_file({
            //       url: '/report/download',
            //       data: {data: JSON.stringify(response)},
            //       complete: framework.unblockUI,
            //       error: c.rpc_error.bind(c),
            //       success: function () {
            //           if (action && options && !action.dialog) {
            //               options.on_close();
            //           }
            //       },
            //   });
            return window.location.href = '/report_qweb_pdf_print/static/src/lib/viewerjs-0.5.8/index.html#';
        } else {
          this._super(action, options);
        }
      });
    }
  }
});

});

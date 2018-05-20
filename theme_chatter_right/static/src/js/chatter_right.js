odoo.define('theme_chatter_right.Chatter', function (require) {
  'use strict';
  /*
   * Theme Chatter Right
   * GNU Public License
   * Alexandre Díaz <dev@redneboa.es>
   */

  var MailChatter = require('mail.Chatter');

  MailChatter.include({
    start: function() {
      this._super.apply(this, arguments);

      if (this.$el.css('visibility') === 'hidden'|| this.$el.css('display') === 'none' || this.view.ViewManager.$modal) {
        this.view.$el.find('.o_form_sheet_bg').removeClass("o_form_sheet_chatter_right");
        this.$el.removeClass('o_chatter_right');
      } else {
        this.view.$el.find('.o_form_sheet_bg').addClass("o_form_sheet_chatter_right");
        this.$el.addClass('o_chatter_right');
      }
    }
  });

});

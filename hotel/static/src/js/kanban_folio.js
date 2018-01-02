openerp.hotel_folio_kanban_colouring = function (instance) {
instance.web_kanban.KanbanRecord.include({
        kanban_getcolor: function (variable) {
            if (this.view.fields_view.model == 'hotel.folio') {
                return (0 % this.view.number_of_color_schemes);
            } else {
                return this._super(variable);
            }
        },
        renderElement: function () {
            this._super();
            if (this.values.color) {
                this.$el.find('.oe_kanban_details').css("background-color", this.values.color.value || 'white');
            }
        }
    });
};


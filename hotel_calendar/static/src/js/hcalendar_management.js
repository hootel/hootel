/* global _, moment */
'use strict';
/*
 * Hotel Calendar Management JS v0.0.1a - 2017
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 *
 * Dependencies:
 *     - moment
 *     - underscore
 */

function HotelCalendarManagement(/*String*/querySelector, /*Dictionary*/options, /*HTMLObject?*/_base) {
  if (window === this) {
    return new HotelCalendarManagement(querySelector, options, _base);
  }

  this.$base = (_base === 'undefined') ? document : _base;

  if (typeof querySelector === 'string') {
    this.e = this.$base.querySelector(querySelector);
    if (!this.e) {
      return false;
    }
  } else if (typeof querySelector === 'object') {
    this.e = querySelector;
  } else {
    return {
      Version: '0.0.1a',
      Author: "Alexandre Díaz",
      Created: "24/09/2017",
      Updated: ""
    };
  }

  /** Options **/
  if (!options) { options = {}; }
  this.options = {
    startDate: moment(options.startDate || new Date()),
    days: options.days || moment(options.startDate || new Date()).daysInMonth(),
    rooms: options.rooms || [],
    endOfWeek: options.endOfWeek || 6,
    currencySymbol: options.currencySymbol || '€',
    dateFormatLong: options.dateFormat || 'YYYY-MM-DD HH:mm:ss',
    dateFormatShort: options.dateFormat || 'YYYY-MM-DD'
  };
  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HVRoom)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar Management][init] Invalid Room definiton!");
  }

  /** Internal Values **/
  this.tableCreated = false;
  this._pricelist = {};
  this._restrictions = {};
  this._availability = {};

  /***/
  if (!this._create()) {
    return false;
  }

  return this;
}

HotelCalendarManagement.prototype = {
  /** PUBLIC MEMBERS **/
  addEventListener: function(/*String*/event, /*Function*/callback) {
    this.e.addEventListener(event, callback);
  },

  //==== CALENDAR
  setStartDate: function(/*String,MomentObject*/date, /*Int?*/days) {
    var curDate = this.options.startDate;
    if (moment.isMoment(date)) {
      this.options.startDate = date;
    } else if (typeof date === 'string'){
      this.options.startDate = moment(date);
    } else {
      console.warn("[Hotel Calendar Management][setStartDate] Invalid date format!");
      return;
    }

    if (typeof days !== 'undefined') {
      this.options.days = days;
    }

    /*this.e.dispatchEvent(new CustomEvent(
            'hcOnChangeDate',
            {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));*/
    this._updateView();
  },

  getOptions: function(/*String?*/key) {
    if (typeof key !== 'undefined') {
      return this.options[key];
    }
    return this.options;
  },


  /** PRIVATE MEMBERS **/
  //==== MAIN FUNCTIONS
  _create: function() {
    this.e.innerHTML = "";
    if (this.tableCreated) {
      console.warn("[Hotel Calendar Management] Already created!");
      return false;
    }

    /** Main Table **/
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-management-table');
    this.etable.classList.add('noselect');
    this.e.appendChild(this.etable);
    this._updateView();
    this.tableCreated = true;

    return true;
  },

  _generateTableDay: function(/*HTMLObject*/parentCell) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-management-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var telm = false;
    var roomId = $this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`).dataset.hcalRoomObjId;
    var room = $this.getRoom(roomId);
    var dateCell = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);
    var dateShortStr = dateCell.format(HotelCalendarManagement._DATE_FORMAT_SHORT);

    row = table.insertRow();

    cell = row.insertCell();
    cell.setAttribute('colspan', '2');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`PRICE_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'price');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Price');
    telm.value = room.price;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);
    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`AVAIL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'avail');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Availability');
    telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    row = table.insertRow();

    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MIN_STAY_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'min_stay');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Min. Stay');
    telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);
    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MIN_STAY_ARRIVAL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'min_stay_arrival');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Min. Stay Arrival');
    telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);
    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MAX_STAY_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'max_stay');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Max. Stay');
    telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    row = table.insertRow();

    cell = row.insertCell();
    cell.setAttribute('colspan', '2');
    telm = document.createElement("select");
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    telm.setAttribute('id', this._sanitizeId(`CLOUSURE_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'clousure');
    telm.setAttribute('title', 'Closure');
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    var selectOpt = document.createElement("option");
    selectOpt.value = "open";
    selectOpt.textContent = "Open";
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed";
    selectOpt.textContent = "Closed";
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed_departure";
    selectOpt.textContent = "C. Departure";
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed_arrival";
    selectOpt.textContent = "C. Arrival";
    telm.appendChild(selectOpt);
    cell.appendChild(telm);
    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`RESERVED_ROOMS_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'reserved_rooms');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', 'Reserved Rooms');
    telm.setAttribute('readonly', 'readonly');
    telm.setAttribute('disabled', 'disabled');
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    cell.appendChild(telm);

    row = table.insertRow();
    cell = row.insertCell();
    cell.style.textAlign = 'center';
    cell.setAttribute('colspan', '3');
    telm = document.createElement("button");
    telm.setAttribute('id', this._sanitizeId(`NO_OTA_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'no_ota');
    telm.setAttribute('title', 'No OTA');
    telm.innerHTML = "<strong>No OTA</strong>";
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('click', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);


    parentCell.appendChild(table);

    return table;
  },

  setData: function(prices, restrictions, avail) {
    this._updateView();
    if (typeof prices !== 'undefined' && prices) {
      this._setPricelist(prices);
    }
    if (typeof restrictions !== 'undefined' && restrictions) {
      this._setRestrictions(restrictions);
    }
    if (typeof avail !== 'undefined' && avail) {
      this._setAvailability(avail);
    }
  },

  //==== ROOMS
  getRoom: function(/*String*/id) {
    return _.find(this.options.rooms, function(item){ return item.id == id; });
  },

  //==== RENDER FUNCTIONS
  _create_table_reservation_days: function() {
    var $this = this;
    this.etable.innerHTML = "";
    /** TABLE HEADER **/
    var thead = this.etable.createTHead();
    var row = thead.insertRow();
    var row_init = row;

    var cell = row.insertCell();
    cell.setAttribute('rowspan', 2);
    cell.setAttribute('colspan', 2);
    cell.setAttribute('class', 'col-xs-1 col-lg-1');

    // Render Next Days
    row = thead.insertRow();
    var months = { };
    var cur_month = this.options.startDate.format("MMMM");
    months[cur_month] = {};
    months[cur_month].year = this.options.startDate.format("YYYY");
    months[cur_month].colspan = 0;
    var now = moment().local();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
      cell.textContent = dd.format('D') + ' ' + dd.format('ddd');
      cell.setAttribute('title', dd.format('dddd'))
      var day = +dd.format('D');
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
        cur_month = dd.format('MMMM');
        months[cur_month] = {};
        months[cur_month].year = dd.format('YYYY');
        months[cur_month].colspan = 0;
      }
      if (dd.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd.format('e') == this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
      ++months[cur_month].colspan;
    }
    // Render Months
    var month_keys = Object.keys(months);
    for (var m of month_keys) {
      var cell_month = row_init.insertCell();
      cell_month.setAttribute('colspan', months[m].colspan);
      cell_month.innerText = m+' '+months[m].year;
      cell_month.classList.add('hcal-cell-month');
      cell_month.classList.add('btn-hcal');
      cell_month.classList.add('btn-hcal-3d');
    }

    /** ROOM LINES **/
    var tbody = document.createElement("tbody");
    this.etable.appendChild(tbody);
    this.options.rooms.forEach(function(itemRoom, indexRoom){
      // Room Number
      row = tbody.insertRow();
      row.setAttribute('id', $this._sanitizeId(`ROW_${itemRoom.name}_${indexRoom}`));
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      cell = row.insertCell();
      cell.textContent = itemRoom.name;
      cell.setAttribute('colspan', 2);
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      for (var i=0; i<=$this.options.days; i++) {
        var dd = $this.options.startDate.clone().add(i,'d');
        cell = row.insertCell();
        cell.setAttribute('id', $this._sanitizeId(`${itemRoom.name}_${indexRoom}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        // Generate Interactive Table
        cell.appendChild($this._generateTableDay(cell));
        //cell.innerHTML = dd.format("DD");
        var day = +dd.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        } else if (dd.format('e') == $this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
    });
  },

  //==== PRICELIST
  _setPricelist: function(/*List*/pricelist) {
    this._pricelist = pricelist;
    var keys = Object.keys(pricelist);
    for (var vroomId of keys) {
      for (var price of pricelist[vroomId]) {
        var dd = HotelCalendarManagement.toMoment(price.date, this.options.dateFormatShort);
        var inputId = this._sanitizeId(`PRICE_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`);
        var input = this.etable.querySelector(`#${inputId}`);
        if (input) {
          input.dataset.orgValue = price.price;
          input.value = price.price;
        }
      }
    }
  },

  getPricelist: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputId = this._sanitizeId(`PRICE_${room.id}_${ndateStr}`);
        var input = this.etable.querySelector(`#${inputId}`);
        if (!onlyNew || (onlyNew && input.value !== input.dataset.orgValue)) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'price': input.value
          });
        }
      }
    }
    return data;
  },

  //==== RESTRICTIONS
  _setRestrictions: function(/*List*/restrictions) {
    this._restrictions = restrictions;
    var keys = Object.keys(restrictions);
    for (var vroomId of keys) {
      var room = this.getRoom(vroomId);
      for (var restriction of restrictions[vroomId]) {
        var dd = HotelCalendarManagement.toMoment(restriction.date, this.options.dateFormatShort);
        var inputIds = [
          `MIN_STAY_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, restriction.min_stay,
          `MIN_STAY_ARRIVAL_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, restriction.min_stay_arrival,
          `MAX_STAY_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, restriction.max_stay
        ];

        for (var i=0; i<inputIds.length; i+=2) {
          var inputId = this._sanitizeId(inputIds[i]);
          var input = this.etable.querySelector(`#${inputId}`);
          if (input) {
            input.dataset.orgValue = inputIds[i+1];
            input.value = inputIds[i+1];
            if (i < 2) { // Only min and min arrival
              input.style.backgroundColor = (input.value >= room.capacity)?'yellow':'white';
            }
            else {
              input.style.backgroundColor = (input.value > 0 && input.value != input.dataset.orgValue)?'yellow':'white';
            }
          }
        }

        var inputClousureId = this._sanitizeId(`CLOUSURE_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`);
        var inputClousure = this.etable.querySelector(`#${inputClousureId}`);
        if (inputClousure) {
          inputClousure.dataset.orgValue = inputClousure.value = (restriction.closed && 'closed') ||
                                                          (restriction.closed_arrival && 'closed_arrival') ||
                                                          (restriction.closed_departure && 'closed_departure') || 'open';
        }
      }
    }
  },

  getRestrictions: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputMinStayId = this._sanitizeId(`MIN_STAY_${room.id}_${ndateStr}`);
        var inputMinStay = this.etable.querySelector(`#${inputMinStayId}`);
        var inputMinStayArrivalId = this._sanitizeId(`MIN_STAY_ARRIVAL_${room.id}_${ndateStr}`);
        var inputMinStayArrival = this.etable.querySelector(`#${inputMinStayArrivalId}`);
        var inputMaxStayId = this._sanitizeId(`MAX_STAY_${room.id}_${ndateStr}`);
        var inputMaxStay = this.etable.querySelector(`#${inputMaxStayId}`);
        var inputClousureId = this._sanitizeId(`CLOUSURE_${room.id}_${ndateStr}`);
        var inputClousure = this.etable.querySelector(`#${inputClousureId}`);

        if (!onlyNew || (onlyNew && (inputMinStay.value !== inputMinStay.dataset.orgValue ||
                                      inputMinStayArrival.value !== inputMinStayArrival.dataset.orgValue ||
                                      inputMaxStay.value !== inputMaxStay.dataset.orgValue ||
                                      inputClousure.value !== inputClousure.dataset.orgValue))) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'min_stay': inputMinStay.value,
            'min_stay_arrival': inputMinStayArrival.value,
            'max_stay': inputMaxStay.value,
            'closed': inputClousure.value === 'closed',
            'closed_arrival': inputClousure.value === 'closed_arrival',
            'closed_departure': inputClousure.value === 'closed_departure'
          });
        }
      }
    }
    return data;
  },

  //==== AVAILABILITY
  _setAvailability: function(/*List*/availability) {
    this._availability = availability;
    var keys = Object.keys(availability);
    for (var vroomId of keys) {
      for (var avail of availability[vroomId]) {
        var dd = HotelCalendarManagement.toMoment(avail.date, this.options.dateFormatShort);
        var inputIds = [
          `AVAIL_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.avail,
          `NO_OTA_${vroomId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.no_ota
        ];

        for (var i=0; i<inputIds.length; i+=2) {
          var inputId = this._sanitizeId(inputIds[i]);
          var input = this.etable.querySelector(`#${inputId}`);
          if (input) {
            input.dataset.orgValue = inputIds[i+1];
            if (input.tagName.toLowerCase() === 'button') {
              input.dataset.state = inputIds[i+1];
              input.textContent = inputIds[i+1]?"No OTA!":"No OTA";
              if (inputIds[i+1]) {
                input.classList.add('hcal-management-input-active');
              }
              else {
                input.classList.remove('hcal-management-input-active');
              }
            }
            else {
              input.value = inputIds[i+1];
            }
          }
        }
      }
    }
  },

  getAvailability: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputAvailId = this._sanitizeId(`AVAIL_${room.id}_${ndateStr}`);
        var inputAvail = this.etable.querySelector(`#${inputAvailId}`);
        var inputNoOTAId = this._sanitizeId(`NO_OTA_${room.id}_${ndateStr}`);
        var inputNoOTA = this.etable.querySelector(`#${inputNoOTAId}`);

        if (!onlyNew || (onlyNew && (inputAvail.value !== inputAvail.dataset.orgValue ||
                                      (inputNoOTA.dataset.state && inputNoOTA.dataset.state !== inputNoOTA.dataset.orgValue)))) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'avail': inputAvail.value,
            'no_ota': Boolean(inputNoOTA.dataset.state === 'true') || false
          });
        }
      }
    }
    return data;
  },

  //==== UPDATE FUNCTIONS
  _updateView: function() {
    this._create_table_reservation_days();
  },

  //==== HELPER FUNCTIONS
  _sanitizeId: function(/*String*/str) {
    return str.replace(/[\/\s\+\-]/g, '_');
  },

  _isNumeric: function(/*?*/n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  },

  //==== EVENT FUNCTIONS
  onInputChange: function(/*EventObject*/ev, /*HTMLObject*/elm) {
    var parentCell = this.$base.querySelector(`#${elm.dataset.hcalParentCell}`);
    var parentRow = this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`);
    var dateCell = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);
    var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
    var name = elm.getAttribute('name');
    var value = elm.value;
    var orgValue = elm.dataset.orgValue;

    if (elm.getAttribute('type') === 'checkbox') {
      value = elm.checked;
    }
    else if (name === 'min_stay' || name === 'min_stay_arrival' || name === 'max_stay' ||
              name === 'price' || name === 'avail') {
      elm.style.backgroundColor = this._isNumeric(value)?'white':'red';
    }
    else if (elm.tagName.toLowerCase() === 'button') {
      value = Boolean(!(elm.dataset.state === 'true'));
      elm.dataset.state = value;
      if (name === 'no_ota') {
        elm.textContent = value?'No OTA!':'No OTA';
        if (value) {
          elm.classList.add('hcal-management-input-active');
        } else {
          elm.classList.remove('hcal-management-input-active');
        }
      }
    }

    this.e.dispatchEvent(new CustomEvent(
      'hcmOnInputChanged',
      {'detail': {'date': dateCell, 'room': room, 'name': name, 'value': value}}));
  }
};

/** STATIC METHODS **/
HotelCalendarManagement._DATE_FORMAT_LONG = "DD/MM/YYYY HH:mm:ss";
HotelCalendarManagement._DATE_FORMAT_SHORT = "DD/MM/YYYY";
HotelCalendarManagement.toMoment = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment(ndate, typeof format==='undefined'?HotelCalendarManagement._DATE_FORMAT_LONG:format);
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }
  console.warn('[Hotel Calendar][toMoment] Invalid date format!');
  return false;
}


/** ROOM OBJECT **/
function HVRoom(/*Int*/id, /*String*/name, /*Int*/capacity, /*Float*/price) {
  this.id = id || -1;
  this.name = name;
  this.capacity = capacity;
  this.price = price;

  this.userData_ = {};
}
HVRoom.prototype = {
  clearUserData: function() { this.userData_ = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this.userData_;
    }
    return this.userData_[key];
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar Management][HVRoom][setUserData] Invalid Data! Need be a object!");
    } else {
      this.userData_ = _.extend(this.userData_, data);
    }
  },
};

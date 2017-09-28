/* global _, moment */
'use strict';
/*
 * Hotel Calendar JS v0.0.1a - 2017
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 *
 * Dependencies:
 *     - moment
 *     - underscore
 */

function HotelCalendar(/*String*/querySelector, /*Dictionary*/options, /*List*/pricelist, /*HTMLObject?*/_base) {
  if (window === this) {
    return new HotelCalendar(querySelector, options, pricelist, _base);
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
      Created: "20/04/2017",
      Updated: ""
    };
  }

  /** Options **/
  console.log(options.startDate);
  if (!options) { options = {}; }
  this.options = {
    startDate: moment(options.startDate || new Date()).subtract('1', 'd'),
    days: (options.days + 1) || (moment(options.startDate || new Date()).daysInMonth() + 1),
    rooms: options.rooms || [],
    showPaginator: options.showPaginator || false,
    allowInvalidActions: options.allowInvalidActions || false,
    assistedMovement: options.assistedMovement || false,
    endOfWeek: options.endOfWeek || 6,
    currencySymbol: options.currencySymbol || '€'
  };

  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar][init] Invalid Room definiton!");
  }

  /** Internal Values **/
  this.isNRerservation = true;
  this._pricelist = pricelist || [];
  this.reservations = [];
  this.tableCreated = false;
  this.cellSelection = {start:false, end:false, current:false};
  this.numRooms = this.options.rooms.length;
  /** Constants **/
  this.ACTION = { NONE: -1, MOVE_ALL: 0, MOVE_LEFT: 1, MOVE_RIGHT: 2 };

  /***/
  this.reset_action_reservation_();
  if (!this.create_()) {
    return false;
  }

  /** Main Events **/
  document.addEventListener('mouseup', this.onMainMouseUp.bind(this), false);
  window.addEventListener('resize', this.onMainResize.bind(this), false);

  return this;
}

HotelCalendar.prototype = {
  /** PUBLIC MEMBERS **/
  addEventListener: function(/*String*/event, /*Function*/callback) {
    this.e.addEventListener(event, callback);
  },

  //==== CALENDAR
  setStartDate: function(/*String,MomentObject*/date, /*Int?*/days) {
    if (moment.isMoment(date)) {
      this.options.startDate = date.subtract('1','d');
    } else if (typeof date === 'string'){
      this.options.startDate = moment(date).subtract('1','d');
    } else {
      console.warn("[Hotel Calendar][setStartDate] Invalid date format!");
      return;
    }

    if (typeof days !== 'undefined') {
      this.options.days = days + 1;
    }

    /*this.e.dispatchEvent(new CustomEvent(
            'hcOnChangeDate',
            {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));*/
    this.updateView_();
  },

  advance: function(/*Int*/amount, /*Char*/step) {
    var $this = this;
    var curDate = this.options.startDate.clone();
    this.options.startDate.add(amount, step);
    this.updateView_();
    this.e.dispatchEvent(new CustomEvent(
      'hcOnChangeDate',
      {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));
  },

  back: function(/*Int*/amount, /*Char*/step) {
    var $this = this;
    var cur_date = this.options.startDate.clone();
    this.options.startDate.subtract(amount, step);
    this.updateView_();
    this.e.dispatchEvent(new CustomEvent(
      'hcOnChangeDate',
      {'detail': {'prevDate':cur_date, 'newDate': $this.options.startDate}}));
  },

  getOptions: function(/*String?*/key) {
    if (typeof key !== 'undefined') {
      return this.options[key];
    }
    return this.options;
  },

  //==== RESERVATIONS
  clearReservationDivs: function() {
    var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
    for (var i=reservs.length; i>0; this.e.removeChild(reservs[--i]));
  },

  getReservations: function(/*HReservation*/ignoreThis) {
    return _.reject(this.reservations, function(item){ return item===ignoreThis; });
  },

  getReservation: function(/*Int*/id) {
    return _.find(this.reservations, {'id': +id});
  },

  getReservationDiv: function(/*HReservationObject*/reservationObj) {
    var reservDiv = this.e.querySelector(`.hcal-reservation[data-hcal-reservation-obj-id='${reservationObj.id}']`);
    return reservDiv;
  },

  setReservations: function(/*List*/reservations) {
    var ids = _.pluck(this.reservations, 'id');
    for (var id of ids) {
      this.removeReservation(id, true);
    }
    this.reservations = [];
    this.addReservations(reservations);
  },

  addReservations: function(/*List*/reservations) {
    if (reservations.length > 0 && !(reservations[0] instanceof HReservation)) {
      console.warn("[HotelCalendar][setReservations] Invalid Reservation definition!");
    } else {
      // Merge
      for (var reserv of reservations) {
        var index = _.findKey(this.reservations, {'id': reserv.id});
        if (index) {
          this.reservations[index] = reserv;
        } else {
          this.reservations.push(reserv);
          index = this.reservations.length;
        }

        var divRes = this.getReservationDiv(reserv);
        if (divRes) {
          divRes.innerText = reserv.title;
          // this.updateDivReservation_(divRes, limits);
          if (reserv.readOnly) {
            divRes.classList.add('hcal-reservation-readonly');
          } else {
            divRes.classList.remove('hcal-reservation-readonly');
          }
        } else {
          var limits = this.getReservationCellLimits(reserv);
          if (limits.isValid()) {
            divRes = document.createElement('div');
            divRes.dataset.hcalReservationObjId = reserv.id;
            divRes.classList.add('hcal-reservation');
            divRes.classList.add('noselect');
            divRes.innerText = reserv.title;
            // this.updateDivReservation_(divRes, limits);
            this.e.appendChild(divRes);

            if (reserv.readOnly) {
              divRes.classList.add('hcal-reservation-readonly');
            }
            this.assignReservationsEvents_([divRes]);
          }
        }
      }

      this.isNRerservation = true;
      this.updateReservations_();
    }
  },

  removeReservation: function(/*Int*/reservationID, /*Boolean?*/noupdate) {
    var reserv = _.find(this.reservations, {'id': reservationID});
    if (reserv) {
      var resDiv = this.getReservationDiv(reserv);
      if (resDiv) {
        resDiv.parentNode.removeChild(resDiv);
      }
      this.reservations = _.without(this.reservations, reserv);
      this.isNRerservation = true;
      if (!noupdate) {
        this.updateReservations_();
      }
    }
  },

  getReservationsByDay: function(/*String,MomentObject*/day, /*Bool*/strict, /*Int?*/nroom, /*Int?*/nbed) {
    var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
        return false;
    }

    var reservs = [];
    for (var r of this.reservations) {
      if ((day.isBetween(r.startDate, r.endDate, 'day')
          || (strict && day.isSame(r.startDate, 'day')))
        && (typeof nroom === 'undefined' || r.room.number == nroom)
        && (typeof nbed === 'undefined' || r.beds_.includes(nbed))) {
        reservs.push(r);
      }
    }

    return reservs;
  },

  getReservationCellLimits: function(/*HReservationObject*/reservation, /*Int?*/nbed, /*Bool?*/notCheck) {
    var limits = new HLimit();

    console.log("CALCULATING POSITOIN");

    var bedNum = 0;
    if (typeof nbed === 'undefined') {
      bedNum = (reservation.beds_&&reservation.beds_.length)?reservation.beds_[0]:0;
    } else {
      bedNum = nbed;
    }

    var diff_date = reservation.endDate.diff(reservation.startDate, 'days');
    var rpersons = reservation.room.shared?reservation.room.capacity:1;
    var cellFound = false;
    var cellStartType = '';
    var cellEndType = '';

    // Search Initial Cell
    var cell = this.getCell(reservation.startDate.clone().startOf('day'),
                            reservation.room.type,
                            reservation.room.number,
                            bedNum);
    if (!cell) {
      var date = reservation.startDate.clone().startOf('day');
      for (var i=0; i<diff_date; i++) {
        cell = this.getCell(
          date.add(1, 'd'),
          reservation.room.type,
          reservation.room.number,
          bedNum);
        if (cell) {
          cellStartType = 'soft-start';
          limits.left = cell;
          break;
        }
      }
    } else {
      cellStartType = 'hard-start';
      limits.left = cell;
    }

    // More Beds?
    var reservPersons = reservation.getTotalPersons();
    if (reservation.room.shared && reservPersons > 1 && bedNum+reservPersons <= rpersons) {
      bedNum += reservPersons-1;
    }

    // Search End Cell
    var cell = this.getCell(reservation.endDate.clone().endOf('day'),
                            reservation.room.type,
                            reservation.room.number,
                            bedNum);
    if (!cell) {
      var date = reservation.endDate.clone().endOf('day');
      for (var i=0; i<diff_date; i++) {
        cell = this.getCell(
          date.subtract(1, 'd'),
          reservation.room.type,
          reservation.room.number,
          bedNum);
        if (cell) {
          cellEndType = 'soft-end';
          limits.right = cell;
          break;
        }
      }
    } else {
      cellEndType = 'hard-end';
      limits.right = cell;
    }

    // Exists other reservation in the same place?
    if (!notCheck && limits.isValid()) {
      var limitLeftDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
      var limitRightDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
      var diff_date = limitRightDate.diff(limitLeftDate, 'days');
      var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
      var parentRow = this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`);
      var ndate = HotelCalendar.toMoment(parentRow.dataset.hcalDate).startOf('day').subtract(1, 'd');
      for (var i=0; i<diff_date; i++) {
        ndate.add(1, 'd');
        for (var b=0; b<=numBeds; b++) {
          var reservs = this.getReservationsByDay(ndate, false, reservation.room.number, +limits.left.dataset.hcalBedNum+b);
          reservs = _.reject(reservs, function(item){ return item===reservation; });
          if (reservs.length && !reservs[0].endDate.isSame(ndate, 'day')) {
              return this.getReservationCellLimits(reservation, nbed?nbed+1:1); // Recursive: Search best place
          }
        }
      }

      limits.left.dataset.hcalReservationCellType = cellStartType;
      limits.right.dataset.hcalReservationCellType = cellEndType;
    }

    return limits;
  },

  //==== CELLS
  getCell: function(/*MomentObject*/date, /*String*/type, /*String*/number, /*Int*/bednum) {
    var elms = this.etable.querySelectorAll("td[data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'] table td[data-hcal-bed-num='"+bednum+"']");
    for (var i=0; i<elms.length; i++) {
      var parentRow = this.$base.querySelector(`#${elms[i].dataset.hcalParentRow}`);
      if (parentRow) {
        var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
        if (room && room.type == type && room.number == number) {
          return elms[i];
        }
      }
    }

    return false;
  },

  getCells: function(/*HLimitObject*/limits) {
    var parentRow = this.$base.querySelector(`#${limits.left.dataset.hcalParentRow}`);
    var parentCell = this.$base.querySelector(`#${limits.left.dataset.hcalParentCell}`);
    if (!parentRow || !parentCell) {
      return [];
    }
    var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
    var start_date = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
    var end_date = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
    var diff_date = end_date.diff(start_date, 'days');

    var cells = [];
    var numBeds = +limits.right.dataset.hcalBedNum-+limits.left.dataset.hcalBedNum;
    for (var nbed=0; nbed<=numBeds; nbed++) {
      var date = start_date.clone();
      var cell = this.getCell(date, room.type, room.number, +limits.left.dataset.hcalBedNum+nbed);
      if (cell) {
        cells.push(cell);
      }
      for (var i=0; i<diff_date; i++) {
        cell = this.getCell(
          date.add(1, 'd'),
          room.type,
          room.number,
          +limits.left.dataset.hcalBedNum+nbed);
        if (cell) {
          cells.push(cell);
        }
      }
    }
    return cells;
  },

  //==== ROOMS
  getDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    var reservs = this.getReservationsByDay(day, true);
    return _.filter(reservs, function(item){ return item.room.type === room_type; });
  },

  getRoomsByType: function(/*String*/type) {
    return _.filter(this.options.rooms, function(item){ return item.type === type; });
  },

  getRoomsCapacityByType: function(/*String*/type) {
    var trooms = this.getRoomsByType(type);
    var num_rooms = 0;
    for (var tr of trooms) {
      num_rooms += tr.shared?tr.capacity:1;
    }
    return num_rooms;
  },

  getRoomsCapacityTotal: function() {
    var num_rooms = 0;
    for (var tr of this.options.rooms) {
      num_rooms += tr.shared?tr.capacity:1;
    }
    return num_rooms;
  },

  getRoomTypes: function() {
    return _.uniq(_.pluck(this.options.rooms, 'type'));
  },

  getRoom: function(/*String*/id) {
    return _.find(this.options.rooms, function(item){ return item.id == id; });
  },

  getRoomPrice: function(/*String*/id, /*String,MomentObject*/day) {
    var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
      return 0.0;
    }

    var room = this.getRoom(id);
    if (room.price[0] == 'fixed') {
      return room.price[1];
    } else if (room.price[0] == 'pricelist'){
      var price_input = this.edtable.querySelector('#'+this.sanitizeId_(`CELL_PRICE_${room.price[2]}_${room.price[1]}_${day.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      return parseFloat(price_input.textContent.replace(",", "."));
    }

    return 0.0;
  },

  //==== DETAIL CALCS
  calcDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
      return false;
    }

    var reservs = this.getDayRoomTypeReservations(day, room_type);
    var num_rooms = this.getRoomsCapacityByType(room_type);
    for (var r of reservs) {
      num_rooms -= r.room.shared?r.getTotalPersons():1;
    }

    return num_rooms;
  },

  calcDayRoomTotalReservations: function(/*String,MomentObject*/day) {
    var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
      return false;
    }

    var reservs = this.getReservationsByDay(day, true);
    var num_rooms = this.getRoomsCapacityTotal();
    for (var r of reservs) {
      num_rooms -= r.room.shared?r.getTotalPersons():1;
    }

    return num_rooms;
  },

  calcReservationOccupation: function(/*String,MomentObject*/day, /*String*/room_type) {
    var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
      return false;
    }

    var reservs = this.getReservationsByDay(day, true);
    return Math.round(reservs.length/this.numRooms*100.0);
  },



  /** PRIVATE MEMBERS **/
  //==== MAIN FUNCTIONS
  reset_action_reservation_: function() {
    this.reservationAction = {
      action: this.ACTION.NONE,
      reservation: null,
      oldReservationObj: null,
      newReservationObj: null
    };
  },

  create_: function() {
    this.e.innerHTML = "";
    if (this.tableCreated) {
      console.warn("[Hotel Calendar] Already created!");
      return false;
    }

    /** Main Table **/
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-table');
    this.etable.classList.add('noselect');
    this.edtable = document.createElement("table");
    this.edtable.classList.add('hcal-table');
    this.edtable.classList.add('noselect');
    this.e.appendChild(this.etable);
    this.e.appendChild(this.edtable);
    this.updateView_();
    this.tableCreated = true;

    return true;
  },

  generateTableDay_: function(/*HTMLObject*/parentCell) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var roomNumber = $this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`).dataset.hcalRoomObjId;
    var room = $this.getRoom(roomNumber);
    var num = (room.shared?room.capacity:1);
    for (var i=0; i<num; i++) {
      row = table.insertRow();
      cell = row.insertCell();
      cell.dataset.hcalParentRow = parentCell.dataset.hcalParentRow;
      cell.dataset.hcalParentCell = parentCell.getAttribute('id');
      cell.dataset.hcalBedNum = i;
      cell.addEventListener('mouseenter', function(ev){
        var date_cell = HotelCalendar.toMoment($this.etable.querySelector(`#${this.dataset.hcalParentCell}`).dataset.hcalDate);
        if ($this.isLeftButtonPressed_(ev)) {
          var reserv = null;
          var toRoom = undefined;
          var needUpdate = false;
          if (!$this.reservationAction.reservation) {
            if ($this.cellSelection.start && $this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow) {
              $this.cellSelection.current = this;
            }
            $this.updateCellSelection_();
          } else if ($this.reservationAction.action == $this.ACTION.MOVE_RIGHT) {
            reserv = $this.getReservation($this.reservationAction.reservation.dataset.hcalReservationObjId);
            if (reserv.fixDays) {
              $this.reset_action_reservation_();
              return true;
            }
            if (!date_cell.isAfter(reserv.startDate.clone().startOf('day'))) {
              date_cell = reserv.startDate.clone().startOf('day').add(1, 'd');
            }
            if (!$this.reservationAction.oldReservationObj) {
              $this.reservationAction.oldReservationObj = _.clone(reserv);
              $this.reservationAction.oldReservationObj.startDate = reserv.startDate.clone();
              $this.reservationAction.oldReservationObj.endDate = reserv.endDate.clone();
            }
            reserv.endDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
            $this.reservationAction.newReservationObj = reserv;
            needUpdate = true;
          } else if ($this.reservationAction.action == $this.ACTION.MOVE_LEFT) {
            reserv = $this.getReservation($this.reservationAction.reservation.dataset.hcalReservationObjId);
            if (reserv.fixDays) {
              $this.reset_action_reservation_();
              return true;
            }
            var ndate = reserv.endDate.clone().endOf('day').subtract(1, 'd');
            if (!date_cell.isBefore(ndate)) {
              date_cell = ndate;
            }
            if (!$this.reservationAction.oldReservationObj) {
              $this.reservationAction.oldReservationObj = _.clone(reserv);
              $this.reservationAction.oldReservationObj.startDate = reserv.startDate.clone();
              $this.reservationAction.oldReservationObj.endDate = reserv.endDate.clone();
            }
            reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
            $this.reservationAction.newReservationObj = reserv;
            needUpdate = true;
          } else if ($this.reservationAction.action == $this.ACTION.MOVE_ALL) {
            reserv = $this.getReservation($this.reservationAction.reservation.dataset.hcalReservationObjId);
            if (!$this.reservationAction.oldReservationObj) {
              $this.reservationAction.oldReservationObj = _.clone(reserv);
              $this.reservationAction.oldReservationObj.startDate = reserv.startDate.clone();
              $this.reservationAction.oldReservationObj.endDate = reserv.endDate.clone();
            }
            var parentRow = $this.$base.querySelector(`#${this.dataset.hcalParentRow}`);
            var room = $this.getRoom(parentRow.dataset.hcalRoomObjId);
            reserv.room = room;
            var diff_date = reserv.endDate.diff(reserv.startDate, 'days')+1;
            reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
            var date_end = reserv.startDate.clone().add(diff_date, 'd');
            reserv.endDate.set({'date': date_end.date(), 'month': date_end.month(), 'year': date_end.year()});
            $this.reservationAction.newReservationObj = reserv;
            toRoom = +this.dataset.hcalBedNum;
            needUpdate = true;
          }

          if (needUpdate) {
            var linkedReservations = $this.getLinkedReservations($this.reservationAction.newReservationObj);
            linkedReservations.push(reserv);

            for (var lr of linkedReservations) {
              if (lr!==reserv) {
                lr.startDate = reserv.startDate.clone();
                lr.endDate = reserv.endDate.clone();
              }

              var reservationDiv = $this.getReservationDiv(lr);
              if (reservationDiv) {
                var limits = $this.getReservationCellLimits(
                  lr,
                  lr===reserv?toRoom:undefined,
                  !$this.options.assistedMovement);
                $this.updateDivReservation_(reservationDiv, limits);

                if (!$this.checkReservationPlace(lr) || !limits) {
                  reservationDiv.classList.add('hcal-reservation-invalid');
                } else {
                  reservationDiv.classList.remove('hcal-reservation-invalid');
                }

                if (lr.fixRooms && $this.reservationAction.oldReservationObj.room.id != lr.room.id) {
                  reservationDiv.classList.add('hcal-reservation-invalid');
                }
                if (lr.fixDays && !$this.reservationAction.oldReservationObj.startDate.isSame(lr.startDate, 'day')) {
                  reservationDiv.classList.add('hcal-reservation-invalid');
                }
              }
            }
          }
        }
      }, false);
      cell.addEventListener('mousedown', function(ev){
        $this.cellSelection.start = $this.cellSelection.current = this;
        $this.cellSelection.end = false;
        $this.updateCellSelection_();
      }, false);
      cell.addEventListener('mouseup', function(ev){
        if ($this.cellSelection.start
          && $this.cellSelection.start != this
          && $this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow) {
          $this.cellSelection.end = this;

          $this.e.dispatchEvent(new CustomEvent(
            'hcalOnChangeSelection',
            {'detail': {'cellStart':$this.cellSelection.start, 'cellEnd': $this.cellSelection.end}}));
        }
      }, false);
    }

    return table;
  },

  get_normalized_rooms_: function() {
    var rooms = {};
    if (this.options.rooms) {
      var keys = Object.keys(this.options.rooms);

      for (var r of this.options.rooms) {
        rooms[r.number] = [r.type, r.capacity];
      }
    }
    return rooms;
  },

  //==== RENDER FUNCTIONS
  create_table_reservation_days_: function() {
    var $this = this;
    this.etable.innerHTML = "";
    /** TABLE HEADER **/
    var thead = this.etable.createTHead();
    var row = thead.insertRow();
    var row_init = row;
    // Current Date
    var cell = row.insertCell();
    cell.setAttribute('rowspan', 2);
    cell.setAttribute('colspan', 2);
    cell.setAttribute('class', 'col-xs-1 col-lg-1');
    if (this.options.showPaginator) {
      cell.classList.add('hcal-cell-day-selector');
      var str_date = this.options.startDate.format(HotelCalendar.DATE_FORMAT_SHORT_);
      var span = document.createElement('span');
      span.innerHTML = str_date;
      cell.appendChild(span);
      // Switch Span--EditBox
      span.addEventListener('click', function(ev) { $this.onClickSelectorDate(ev, this); });
      // Button Prev Day
      var link = document.createElement("a");
      link.setAttribute('href', '#');
      link.innerHTML = "&laquo";
      link.addEventListener('click', function(ev){
        $this.back('1', 'd');
      });
      cell.insertBefore(link, cell.firstChild);
      // Button Next Day
      link = document.createElement("a");
      link.setAttribute('href', '#');
      link.innerHTML = "&raquo";
      link.addEventListener('click', function(ev){
        $this.advance('1', 'd');
      });
      cell.appendChild(link);
    }

    // Render Next Days
    row = thead.insertRow();
    var months = { };
    var cur_month = this.options.startDate.format("MMMM");
    months[cur_month] = {};
    months[cur_month].year = this.options.startDate.format("YYYY");
    months[cur_month].colspan = 0;
    var now = moment().utc();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      cell = row.insertCell();
      cell.setAttribute('id', this.sanitizeId_(`hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd.local().format('D')}<br/>${dd.local().format('ddd')}`;
      cell.setAttribute('title', dd.local().format('dddd'))
      var day = +dd.local().format('D');
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
        cur_month = dd.local().format('MMMM');
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
      row.setAttribute('id', $this.sanitizeId_(`ROW_${itemRoom.number}_${itemRoom.type}_${indexRoom}`));
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      cell = row.insertCell();
      cell.textContent = itemRoom.number;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell = row.insertCell();
      cell.textContent = itemRoom.type;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-flat');
      for (var i=0; i<=$this.options.days; i++) {
        var dd = $this.options.startDate.clone().add(i,'d');
        cell = row.insertCell();
        cell.setAttribute('id', $this.sanitizeId_(`${itemRoom.type}_${itemRoom.number}_${indexRoom}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
        // Generate Interactive Table
        cell.appendChild($this.generateTableDay_(cell));
        //cell.innerHTML = dd.format("DD");
        var day = +dd.local().format("D");
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

  create_table_detail_days_: function() {
    var $this = this;
    this.edtable.innerHTML = "";
    /** DETAIL DAYS HEADER **/
    var now = moment().local();
    var thead = this.edtable.createTHead();
    var row = thead.insertRow();
    var cell = row.insertCell();
    cell.setAttribute('colspan', 2);
    cell.setAttribute('class', 'col-xs-1 col-lg-1');
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      cell = row.insertCell();
      cell.setAttribute('id', this.sanitizeId_(`hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd.local().format('D')}<br/>${dd.local().format('ddd')}`;
      cell.setAttribute('title', dd.format("dddd"))
      var day = +dd.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd.format('e') == this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    /** DETAIL LINES **/
    var tbody = document.createElement("tbody");
    this.edtable.appendChild(tbody);
    // Rooms Free Types
    if (this.options.rooms) {
      var room_types = this.getRoomTypes();
      for (var rt of room_types) {
        row = tbody.insertRow();
        row.setAttribute('id', this.sanitizeId_(`ROW_DETAIL_FREE_TYPE_${rt}`));
        row.dataset.hcalRoomType = rt;
        row.classList.add('hcal-row-detail-room-free-type-group-item');
        cell = row.insertCell();
        cell.textContent = rt;
        cell.classList.add('hcal-cell-detail-room-free-type-group-item');
        cell.classList.add('btn-hcal');
        cell.classList.add('btn-hcal-flat');
        cell.setAttribute("colspan", "2");
        for (var i=0; i<=this.options.days; i++) {
          var dd = this.options.startDate.clone().add(i,'d');
          cell = row.insertCell();
          cell.setAttribute('id', this.sanitizeId_(`CELL_FREE_${rt}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
          cell.dataset.hcalParentRow = row.getAttribute('id');
          cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
          cell.textContent = '0';
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
      }
    }
    // Total Free
    row = tbody.insertRow();
    row.setAttribute('id', "ROW_DETAIL_TOTAL_FREE");
    row.classList.add('hcal-row-detail-room-free-total-group-item');
    cell = row.insertCell();
    cell.textContent = 'FREE TOTAL';
    cell.classList.add('hcal-cell-detail-room-free-total-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-flat');
    cell.setAttribute("colspan", "2");
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      cell = row.insertCell();
      cell.setAttribute('id', this.sanitizeId_(`CELL_DETAIL_TOTAL_FREE_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.textContent = '0';
      var day = +dd.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd.format('e') == this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }
    // Percentage Occupied
    row = tbody.insertRow();
    row.setAttribute('id', "ROW_DETAIL_PERC_OCCUP");
    row.classList.add('hcal-row-detail-room-perc-occup-group-item');
    cell = row.insertCell();
    cell.textContent = '% OCCUP.';
    cell.classList.add('hcal-cell-detail-room-perc-occup-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-flat');
    cell.setAttribute("colspan", "2");
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      cell = row.insertCell();
      cell.setAttribute('id', this.sanitizeId_(`CELL_DETAIL_PERC_OCCUP_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.textContent = '0';
      var day = +dd.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd.format('e') == this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }
    // Rooms Pricelist
    if (this._pricelist) {
      var pricelists_keys = _.keys(this._pricelist)
      for (var key of pricelists_keys) {
        var pricelist = this._pricelist[key]
        for (var listitem of pricelist) {
          row = tbody.insertRow();
          row.setAttribute('id', this.sanitizeId_(`ROW_DETAIL_PRICE_ROOM_${key}_${listitem.room}`));
          row.dataset.hcalPricelist = key;
          row.dataset.hcalRoom = listitem.room
          row.classList.add('hcal-row-detail-room-price-group-item');
          cell = row.insertCell();
          cell.innerHTML = "<marquee behavior='alternate' scrollamount='1' scrolldelay='100'>"+listitem.title + ' ' + this.options.currencySymbol+ '</marquee>';
          cell.classList.add('hcal-cell-detail-room-group-item');
          cell.classList.add('btn-hcal');
          cell.classList.add('btn-hcal-flat');
          cell.setAttribute("colspan", "2");
          for (var i=0; i<=$this.options.days; i++) {
            var dd = this.options.startDate.clone().add(i,'d');
            cell = row.insertCell();
            cell.setAttribute('id', this.sanitizeId_(`CELL_PRICE_${key}_${listitem.room}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
            cell.classList.add('hcal-cell-detail-room-price-group-item-day');
            cell.dataset.hcalParentRow = row.getAttribute('id');
            cell.dataset.hcalDate = dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_);
            var day = +dd.format("D");
            if (day == 1) {
              cell.classList.add('hcal-cell-start-month');
            }
            if (dd.isSame(now, 'day')) {
              cell.classList.add('hcal-cell-current-day');
            } else if (dd.format('e') == $this.options.endOfWeek) {
              cell.classList.add('hcal-cell-end-week');
            }

            var dd_fmrt = dd.format(HotelCalendar.DATE_FORMAT_SHORT_); // Local -> UTC
            cell.textContent = _.has(listitem['days'], dd_fmrt)?listitem['days'][dd_fmrt]:'...';
          }
        }
      }
    }
    // Minimum Stay
    /*row = tbody.insertRow();
    row.setAttribute('id', "ROW_DETAIL_MIN_STAY");
    row.classList.add('hcal-row-detail-room-min-stay-group-item');
    cell = row.insertCell();
    cell.textContent = 'MIN. STAY';
    cell.classList.add('hcal-cell-detail-room-min-stay-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-flat');
    cell.setAttribute("colspan", "2");
    for (var i=0; i<this.options.days; i++) {
        var dd = this.options.startDate.clone().add(i,'d');
        cell = row.insertCell();
        cell.setAttribute('id', `CELL_DETAIL_MIN_STAY_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
        cell.classList.add('hcal-cell-detail-room-min-stay-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
        cell.textContent = '0';
        var day = +dd.format("D");
        if (day == 1) {
            cell.classList.add('hcal-cell-start-month');
        }
        if (this.sameSimpleDate_(dd, now)) {
            cell.classList.add('hcal-cell-current-day');
        } else if (dd.format('e') == this.options.endOfWeek) {
            cell.classList.add('hcal-cell-end-week');
        }
    }*/
  },

  //==== UPDATE FUNCTIONS
  updateView_: function() {
    this.create_table_reservation_days_();
    this.create_table_detail_days_();

    this.updateReservations_();
    this.updateCellSelection_();
  },

  updateHighlightInvalidZones: function(/*HReservation*/reserv) {
    if (typeof reserv === 'undefined') {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.remove('hcal-cell-invalid');
      }
      return;
    }

    var limits = this.getReservationCellLimits(reserv);
    if (reserv.readOnly) {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.add('hcal-cell-invalid');
      }
    } else if (reserv.fixDays) {
      var limitLeftDate = this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitRightDate = this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitLeftDateMoment = HotelCalendar.toMoment(limitLeftDate);
      var limitRightDateMoment = HotelCalendar.toMoment(limitRightDate);
      var diff_date = limitRightDateMoment.diff(limitLeftDateMoment, 'days')+1;
      var date = limitLeftDateMoment.clone().startOf('day');
      var selector = [];
      for (var i=1; i<=diff_date; i++) {
        selector.push("not([data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'])");
        date.add(1, 'd');
      }
      if (selector.length) {
        var elms = this.etable.querySelectorAll(`td:${selector.join(':')}`+ ' table td');
        for (var tdCell of elms) {
          tdCell.classList.add('hcal-cell-invalid');
        }
      }
    } else if (reserv.fixRooms) {
        var parentCell = this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`);
        var parent_row = parentCell.dataset.hcalParentRow;
        var elms = this.etable.querySelectorAll("td:not([data-hcal-parent-row='"+parent_row+"']) table td");
        for (var tdCell of elms) {
          tdCell.classList.add('hcal-cell-invalid');
        }
    }
  },

  //==== SELECTION
  updateCellSelection_: function() {
      // Clear all
      var highlighted_td = this.etable.querySelectorAll('td.hcal-cell-highlight');
      for (var td of highlighted_td) {
        td.classList.remove('hcal-cell-highlight');
        td.textContent = '';
      }

      // Highlight Selected
      if (this.cellSelection.current) {
        this.cellSelection.current.classList.add('hcal-cell-highlight');
      }
      // Highlight Range Cells
      var cells = false;
      var total_price = 0.0;
      var limits = new HLimit(this.cellSelection.start,
                              this.cellSelection.end?this.cellSelection.end:this.cellSelection.current);
      if (limits.isValid()) {
        // Normalize
        // TODO: Multi-Directional Selection. Now only support normal or inverse.
        var limitLeftDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
        var limitRightDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
        if (limitLeftDate.isAfter(limitRightDate)) {
          limits.swap();
        }
        cells = this.getCells(limits);
        for (var c of cells) {
          c.classList.add('hcal-cell-highlight');
          if (this._pricelist && (c === cells[0] || c !== cells[cells.length-1])) {
            var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${c.dataset.hcalParentCell}`).dataset.hcalDate);
            var parentRow = this.$base.querySelector(`#${c.dataset.hcalParentRow}`);
            var room_price = this.getRoomPrice(parentRow.dataset.hcalRoomObjId, date_cell);
            c.textContent = room_price + ' ' + this.options.currencySymbol;
            total_price += room_price;
          }
        }
      }

      this.e.dispatchEvent(new CustomEvent(
        'hcalOnUpdateSelection',
          { 'detail': {
            'limits': limits,
            'cells': cells,
            'old_cells': highlighted_td,
            'totalPrice': total_price
          }
        }));
  },

  resetCellSelection_: function() {
    this.cellSelection = { current: false, end: false, start: false };
  },

  //==== RESERVATIONS
  updateDivReservation_: function(/*HTMLObject*/divRes, /*HLimitObject*/limits) {
    if (!limits || !limits.isValid()) {
      return;
    }

    var dateCellInit = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
    var dateCellEnd = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
    var etableOffset = this.etable.getBoundingClientRect();

    var reserv = this.getReservation(divRes.dataset.hcalReservationObjId);
    var numBeds = (+limits.right.dataset.hcalBedNum)-(+limits.left.dataset.hcalBedNum);
    reserv.beds_ = [];
    for (var i=0; i<=numBeds; reserv.beds_.push(+limits.left.dataset.hcalBedNum+i++));

    var boundsInit = limits.left.getBoundingClientRect();
    var boundsEnd = limits.right.getBoundingClientRect();

    divRes.style = {}; // FIXME: Reset Style. Good method?
    divRes.style.backgroundColor = reserv.color;
    var rgb = this.hexToRGB_(`0x${reserv.color.substr(1)}`);
    var invColor = this.getInverseColor_(rgb[0]/255, rgb[1]/255, rgb[2]/255);
    divRes.style.color = `rgb(${invColor[0]*255},${invColor[1]*255},${invColor[2]*255})`;

    divRes.style.top = `${boundsInit.top-etableOffset.top}px`;
    var divHeight = (boundsEnd.bottom-etableOffset.top)-(boundsInit.top-etableOffset.top);
    divRes.style.height = `${divHeight}px`;
    divRes.style.lineHeight = `${divHeight-3}px`;
    var fontHeight = divHeight/2;
    if (fontHeight > 16) {
      fontHeight = 16;
    }
    divRes.style.fontSize = `${fontHeight}px`;
    if (limits.left.dataset.hcalReservationCellType === 'soft-start'
          || (limits.isSame() && dateCellInit.isSame(this.options.startDate, 'day'))) {
      divRes.style.borderLeftWidth = '0';
      divRes.style.borderTopLeftRadius = '0';
      divRes.style.borderBottomLeftRadius = '0';
      divRes.style.left = `${boundsInit.left-etableOffset.left}px`;
      divRes.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0}px`;
    } else if (limits.right.dataset.hcalReservationCellType !== 'soft-end') {
      var offsetLeft = !limits.isSame()?boundsEnd.width/2.0:0;
      divRes.style.left = `${(boundsInit.left-etableOffset.left)+offsetLeft}px`;
      divRes.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0}px`;
    }
    if (limits.right.dataset.hcalReservationCellType === 'soft-end') {
      divRes.style.borderRightWidth = '0';
      divRes.style.borderTopRightRadius = '0';
      divRes.style.borderBottomRightRadius = '0';
      divRes.style.left = `${(boundsInit.left-etableOffset.left)+boundsInit.width/2.0}px`;
      divRes.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0}px`;
    } else if (limits.left.dataset.hcalReservationCellType !== 'soft-start' && !limits.isSame()) {
      divRes.style.width = `${boundsEnd.left-boundsInit.left}px`;
    }
  },

  swapReservation: function(/*HReservationObject*/reservationObj, /*HReservationObject*/newReservationObj) {
      var reservationDiv = this.getReservationDiv(reservationObj);
      if (!reservationDiv) {
        console.warn("[Hotel Calendar][updateReservation_] Invalid Reservation Object");
        return;
      }

      var index = _.findKey(this.reservations, {'id': reservationObj.id});
      delete this.reservations[index];
      this.reservations[index] = newReservationObj;
      reservationDiv.dataset.hcalReservationObjId = newReservationObj.id;
      var limits = this.getReservationCellLimits(newReservationObj);
      this.updateDivReservation_(reservationDiv, limits);

      var linkedReservations = this.getLinkedReservations(newReservationObj);
      for (var lr of linkedReservations) {
        lr.startDate = newReservationObj.startDate.clone();
        lr.endDate = newReservationObj.endDate.clone();

        var reservationDiv = this.getReservationDiv(lr);
        if (reservationDiv) {
          var limits = this.getReservationCellLimits(lr);
          this.updateDivReservation_(reservationDiv, limits);
        }
      }
      this.updateReservationOccupation_();
  },

  setDetailPrice: function(/*String*/room_type, /*String*/date, /*Float*/price) {
    var dd = HotelCalendar.toMomentUTC(date);
    var selector = this.sanitizeId_(`#CELL_PRICE_${room_type}_${dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_)}`);
    var cell_input = this.edtable.querySelector(`${selector} input`);
    cell_input.value = price;
  },

  getLinkedReservations: function(/*HReservationObject*/reservationObj) {
    return _.reject(this.reservations, function(item){ return item === reservationObj || item.id !== reservationObj.id; });
  },

  updateReservations_: function() {
      var $this = this;
      //this.clearReservationDivs();

      var errors = [];
      this.reservations.forEach(function(itemReserv, indexReserv){
        var limits = $this.getReservationCellLimits(itemReserv);

        // Fill
        if (limits.isValid()) {
          var divRes = $this.getReservationDiv(itemReserv);
          $this.updateDivReservation_(divRes, limits);
        } else {
          console.warn(`[Hotel Calendar][updateReservations_] Can't place reservation ID@${itemReserv.id}`);
          errors.push(itemReserv.id);
        }
      });

      // Delete Reservations with errors
      for (var reservID of errors) {
        this.removeReservation(reservID, true);
      }

      //this.assignReservationsEvents_();
      this.updateReservationOccupation_();
      //this.updatePriceList_();

//        if (errors.length && this.isNRerservation) {
//            alert("[Hotel Calendar]\nWARNING: Can't show all reservations!\n\nSee debugger for more details.");
//        }
      this.isNRerservation = false;
  },

  assignReservationsEvents_: function(reservDivs) {
    var $this = this;
    reservDivs = reservDivs || this.e.querySelectorAll('div.hcal-reservation');
    for (var rdiv of reservDivs) {
      var bounds = rdiv.getBoundingClientRect();
      rdiv.addEventListener('mousemove', function(ev){
        var posAction = $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY);
        this.style.cursor = (posAction == $this.ACTION.MOVE_LEFT || posAction == $this.ACTION.MOVE_RIGHT)?'col-resize':'pointer';
      }, false);
      rdiv.addEventListener('mousedown', function(ev){
        if (!$this.reservationAction.reservation && $this.isLeftButtonPressed_(ev)) {
          $this.reservationAction = {
            action: $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY),
            reservation: this
          };

          var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
          console.log("=== RR");
          console.log(reserv);
          $this.updateHighlightInvalidZones(reserv);
          if (reserv.readOnly || (reserv.fixDays && ($this.reservationAction.action == $this.ACTION.MOVE_LEFT ||
                $this.reservationAction.action == $this.ACTION.MOVE_RIGHT))) {
            $this.reservationAction.action = $this.ACTION.NONE;
            return false;
          }
          var linkedReservations = $this.getLinkedReservations(reserv);
          linkedReservations.push(reserv);
          for (var lr of linkedReservations) {
            var reservationDiv = $this.getReservationDiv(lr);
            if (reservationDiv) {
              reservationDiv.classList.add('hcal-reservation-action');
            }
          }

          var otherReservs = _.difference($this.reservations, linkedReservations);
          for (var or of otherReservs) {
            var reservationDiv = $this.getReservationDiv(or);
            if (reservationDiv) {
              reservationDiv.classList.add('hcal-reservation-foreground');
            }
          }
        }
      }, false);
      rdiv.addEventListener('mouseenter', function(ev){
        $this.e.dispatchEvent(new CustomEvent(
          'hcalOnMouseEnterReservation',
          { 'detail': {
              'event': ev,
              'reservationDiv': this,
              'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
            }
          }));
      }, false);
      rdiv.addEventListener('mouseleave', function(ev){
        $this.e.dispatchEvent(new CustomEvent(
          'hcalOnMouseLeaveReservation',
          { 'detail': {
              'event': ev,
              'reservationDiv': this,
              'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
            }
          }));
      }, false);
    }
  },

  getRerservationPositionAction_: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
    var bounds = elm.getBoundingClientRect();
    if (posX <= 5) { return this.ACTION.MOVE_LEFT; }
    else if (posX >= bounds.width-10) { return this.ACTION.MOVE_RIGHT; }
    return this.ACTION.MOVE_ALL;
  },

  updateReservationOccupation_: function() {
    var cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-type-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityByType(parentRow.dataset.hcalRoomType); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTypeReservations(cell_date, parentRow.dataset.hcalRoomType);
      cell.innerText = occup;
      cell.style.backgroundColor = this.generateColor_(occup, num_rooms, 0.35, true, true);
    }

    cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-total-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityTotal(); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTotalReservations(cell_date);
      cell.innerText = occup;
      cell.style.backgroundColor = this.generateColor_(occup, num_rooms, 0.35, true, true);
    }

    cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-perc-occup-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityTotal(); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTotalReservations(cell_date);
      var perc = 100.0 - (occup * 100.0 / num_rooms);
      cell.innerText = perc.toFixed(0);
      cell.style.backgroundColor = this.generateColor_(perc, 100.0, 0.35, false, true);
    }
  },

  //==== PRICELIST
  setPricelist: function(/*List*/pricelist) {
    this._pricelist = pricelist;
    this.updatePriceList_();
  },

  addPricelist: function(/*Dictionary*/pricelist) {
    var keys = _.keys(pricelist);
    for (var k of keys) {
      var pr = pricelist[k];
      for (var pr_k in pr) {
        var pr_item = pricelist[k][pr_k];
        var pr_fk = _.findKey(this._pricelist[k], {'room': pr_item.room});
        if (pr_fk) {
          this._pricelist[k][pr_fk].room = pr_item.room;
          this._pricelist[k][pr_fk].days = _.extend(this._pricelist[k][pr_fk].days, pr_item.days);
          if (pr_item.title) {
            this._pricelist[k][pr_fk].title = pr_item.title;
          }
        } else {
          this._pricelist[k].push({
            'room': pr_item.room,
            'days': pr_item.days,
            'title': pr_item.title
          });
        }
      }
    }
    this.updatePriceList_();
  },

  getPricelist: function(/*Int*/pricelist_id) {
    return this._pricelist[pricelist_id];
  },

  updatePriceList_: function() {
    var keys = _.keys(this._pricelist);
    for (var k of keys) {
      var pr = this._pricelist[k];
      for (var pr_item of pr) {
        var pr_keys = _.keys(pr_item['days']);
        for (var prk of pr_keys) {
          var dd = HotelCalendar.toMomentUTC(prk, HotelCalendar.DATE_FORMAT_SHORT_);
          var price = pr_item['days'][prk];
          var cell = this.edtable.querySelector('#'+this.sanitizeId_(`CELL_PRICE_${k}_${pr_item['room']}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          if (cell) {
            cell.textContent = price;
          }
        }
      }
    }
  },

  //==== HELPER FUNCTIONS
  sanitizeId_: function(/*String*/str) {
    return str.replace(/[\/\s\+\-]/g, '_');
  },

  isLeftButtonPressed_: function(/*EventObject*/evt) {
    evt = evt || window.event;
    if ("buttons" in evt) {
      return evt.buttons == 1;
    }
    var button = evt.which || evt.button;
    return button == 1;
  },

  toAbbreviation: function(/*String*/word, /*Int*/max) {
    return word.replace(/[aeiouáéíóúäëïöü]/gi,'').toUpperCase().substr(0, max || 3);
  },

  checkReservationPlace: function(/*HReservationObject*/reservationObj) {
    var persons = reservationObj.getTotalPersons();
    if ((reservationObj.room.shared && reservationObj.beds_.length < persons)
      || (!reservationObj.room.shared && persons > reservationObj.room.capacity)) {
      return false;
    }

    var reservs = this.getReservations(reservationObj);
    for (var r of reservs) {
      if ((reservationObj.room.number == r.room.number)
        && (_.difference(reservationObj.beds_, r.beds_).length != reservationObj.beds_.length)
        && (!reservationObj.startDate.isSame(r.endDate, 'day'))
        && (!reservationObj.endDate.isSame(r.startDate, 'day'))
        && (r.startDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day')
                || r.endDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day')
                || reservationObj.startDate.isBetween(r.startDate, r.endDate, 'day')
                || reservationObj.endDate.isBetween(r.startDate, r.endDate, 'day')
                || (reservationObj.startDate.isSame(r.startDate)
                        && reservationObj.endDate.isSame(r.endDate)))) {
        return false;
      }
    }

    return true;
  },

  //==== EVENT FUNCTIONS
  onMainMouseUp: function(/*EventObject*/ev) {
    if (this.reservationAction.reservation) {
        var reservDiv = this.reservationAction.reservation;
        reservDiv.classList.remove('hcal-reservation-action');
        this.updateHighlightInvalidZones();

        var rdivs = this.e.querySelectorAll('div.hcal-reservation.hcal-reservation-foreground');
        for (var rd of rdivs) { rd.classList.remove('hcal-reservation-foreground'); }

        var reserv = this.getReservation(reservDiv.dataset.hcalReservationObjId);
        var linkedReservations = this.getLinkedReservations(reserv);
        var hasInvalidLink = false;
        for (var r of linkedReservations) {
          var reservationDiv = this.getReservationDiv(r);
          if (reservationDiv) {
            hasInvalidLink = !hasInvalidLink && reservationDiv.classList.contains('hcal-reservation-invalid');
            reservationDiv.classList.remove('hcal-reservation-action');
            reservationDiv.classList.remove('hcal-reservation-invalid');
          }
        }

        if (this.reservationAction.oldReservationObj && this.reservationAction.newReservationObj) {
          if (!this.options.allowInvalidActions && (reservDiv.classList.contains('hcal-reservation-invalid') || hasInvalidLink)) {
            reservDiv.classList.remove('hcal-reservation-invalid');
            this.swapReservation(this.reservationAction.newReservationObj, this.reservationAction.oldReservationObj);
          } else {
            this.e.dispatchEvent(new CustomEvent(
              'hcalOnChangeReservation',
              { 'detail': {
                  'oldReserv':this.reservationAction.oldReservationObj,
                  'newReserv':this.reservationAction.newReservationObj
                }
              }));
            this.updateReservationOccupation_();
          }
        } else {
          this.e.dispatchEvent(new CustomEvent(
            'hcalOnClickReservation',
            { 'detail': {
                'event': ev,
                'reservationDiv': reservDiv,
                'reservationObj': reserv
              }
            }));
        }
        this.reset_action_reservation_();
    }
    this.resetCellSelection_();
    this.updateCellSelection_();
  },

  onMainResize: function(/*EventObject*/ev) {
    this.updateReservations_();
  },

  onClickSelectorDate: function(/*EventObject*/ev, /*HTMLObject*/elm) {
      var $this = this;
      function setSelectorDate(elm) {
        var new_date = moment(elm.value, HotelCalendar.DATE_FORMAT_SHORT_);
        var span = document.createElement('span');
        span.addEventListener('click', function(ev){ $this.onClickSelectorDate(ev, elm); });
        if (new_date.isValid()) {
          $this.setStartDate(new_date);
        } else {
          $this.setStartDate(moment(new Date()).utc());
        }
      }
      var str_date = this.options.startDate.format(HotelCalendar.DATE_FORMAT_SHORT_);
      var input = document.createElement('input');
      input.setAttribute('id', 'start_date_selector');
      input.setAttribute('type', 'text');
      input.setAttribute('value', str_date);
      input.addEventListener('keypress', function(ev){
        if (ev.keyCode == 13) { // Press Enter
          setSelectorDate(this);
        }
      });
      input.addEventListener('blur', function(ev){ setSelectorDate(this); });
      elm.parentNode.insertBefore(input, elm);
      elm.parentNode.removeChild(elm);
      input.focus();
  },

  //==== COLOR FUNCTIONS (RANGE: 0.0|1.0)
  hueToRgb_: function(/*Int*/v1, /*Int*/v2, /*Int*/h) {
    if (h<0.0) { h+=1; }
    if (h>1.0) { h-=1; }
    if ((6.0*h) < 1.0) { return v1+(v2-v1)*6.0*h; }
    if ((2.0*h) < 1.0) { return v2; }
    if ((3.0*h) < 2.0) { return v1+(v2-v1)*((2.0/3.0)-h)*6.0; }
    return v1;
  },

  hslToRgb_: function(/*Int*/h, /*Int*/s, /*Int*/l) {
    if (s == 0.0) {
      return [l,l,l];
    }
    var v2 = l<0.5?l*(1.0+s):(l+s)-(s*l);
    var v1 = 2.0*l-v2;
    return [
      this.hueToRgb_(v1,v2,h+(1.0/3.0)),
      this.hueToRgb_(v1,v2,h),
      this.hueToRgb_(v1,v2,h-(1.0/3.0))];
  },

  RGBToHex_: function(/*Int*/r, /*Int*/g, /*Int*/b){
    var bin = r << 16 | g << 8 | b;
    return (function(h){
      return new Array(7-h.length).join("0")+h;
    })(bin.toString(16).toUpperCase());
  },

  hexToRGB_: function(/*Int*/hex){
    var r = hex >> 16;
    var g = hex >> 8 & 0xFF;
    var b = hex & 0xFF;
    return [r,g,b];
  },

  getInverseColor_: function(/*Int*/r, /*Int*/g, /*Int*/b) {
      //return this.hslToRgb_(hsl[0], hsl[1], hsl[2]);
    return [1.0-r, 1.0-g, 1.0-b];
  },

  generateColor_: function(/*Int*/value, /*Int*/max, /*Int*/offset, /*Bool*/reverse, /*Bool*/strmode) {
    var rgb = [offset,1.0,0.5];
    if (value > max) {
      if (!strmode) {
        return rgb;
      }
      return "rgb("+Math.floor(rgb[0]*255)+","+Math.floor(rgb[1]*255)+","+Math.floor(rgb[2]*255)+")";
    }
    if (reverse) {
      value = max-value;
    }
    rgb = this.hslToRgb_(((max-value)*offset)/max, 1.0, 0.5);
    if (!strmode) {
      return rgb;
    }
    return "rgb("+Math.floor(rgb[0]*255)+","+Math.floor(rgb[1]*255)+","+Math.floor(rgb[2]*255)+")";
  }
};

/** STATIC METHODS **/
HotelCalendar.DATE_FORMAT_SHORT_ = 'DD/MM/YYYY';
HotelCalendar.DATE_FORMAT_LONG_ = HotelCalendar.DATE_FORMAT_SHORT_ + ' HH:mm:ss';
HotelCalendar.toMoment = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment(ndate, typeof format==='undefined'?HotelCalendar.DATE_FORMAT_LONG_:format);
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }
  console.warn('[Hotel Calendar][toMoment] Invalid date format!');
  return false;
}
HotelCalendar.toMomentUTC = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment.utc(ndate, (typeof format==='undefined'?HotelCalendar.DATE_FORMAT_LONG_:format));
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }
  console.warn('[Hotel Calendar][toMoment] Invalid date format!');
  return false;
}


/** ROOM OBJECT **/
function HRoom(/*Int*/id, /*String*/number, /*Int*/capacity, /*String*/type, /*Bool*/shared, /*List*/price) {
  this.id = id || -1;
  this.number = number || -1;
  this.capacity = capacity || 1;
  this.type = type || '';
  this.shared = shared;
  this.price = price || false;

  this.userData_ = {};
}
HRoom.prototype = {
  clearUserData: function() { this.userData_ = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this.userData_;
    }
    return this.userData_[key];
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HRoom][setUserData] Invalid Data! Need be a object!");
    } else {
      this.userData_ = _.extend(this.userData_, data);
    }
  },
};

/** RESERVATION OBJECT **/
function HReservation(/*Int*/id, /*HRoomObject*/room, /*String?*/title, /*Int?*/adults,
                        /*Int?*/childrens, /*String,MomentObject??*/startDate, /*String,MomentObject??*/endDate,
                        /*String?*/color, /*Boolean?*/readOnly, /*Boolean?*/fixDays, /*Boolean?*/fixRooms) {
  if (typeof room === 'undefined') {
    delete this;
    console.warn("[Hotel Calendar][HReservation] room can't be empty!");
    return;
  }

  this.id = id || -1;
  this.room = room;
  this.adults = adults || 1;
  this.childrens = childrens || 0;
  this.title = title || '';
  this.startDate = startDate || null;
  this.endDate = endDate || null;
  this.color = color || '#000';
  this.readOnly = readOnly || false;
  this.fixDays = fixDays || false;
  this.fixRooms = fixRooms || false;
  
  console.log(startDate);
  console.log(endDate);

  this.beds_ = [];
  this.userData_ = {};
}
HReservation.prototype = {
  setStartDate: function(/*String,MomentObject*/date) { this.startDate = HotelCalendar.toMomentUTC(date); },
  setEndDate: function(/*String,MomentObject*/date) { this.endDate = HotelCalendar.toMomentUTC(date); },

  clearUserData: function() { this.userData_ = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this.userData_;
    }
    return this.userData_[key];
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HReservation][setUserData] Invalid Data! Need be a object!");
    } else {
      this.userData_ = _.extend(this.userData_, data);
    }
  },
  getTotalPersons: function() {
    return this.adults+this.childrens;
  },
};

/** LIMIT OBJECT **/
function HLimit(/*HTMLObject*/left, /*HMTLObject*/right) {
  this.left = left;
  this.right = right;
}
HLimit.prototype = {
  isSame: function() {
    return this.left == this.right;
  },
  isValid: function() {
    return this.left && this.right;
  },
  swap: function() {
    var tt = this.left;
    this.left = this.right;
    this.right = tt;
  }
};

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
  if (!options) { options = {}; }
  this.options = {
    startDate: ((options.startDate && HotelCalendar.toMomentUTC(options.startDate)) || moment(new Date()).utc()).subtract('1', 'd'),
    days: (options.days || ((options.startDate && HotelCalendar.toMomentUTC(options.startDate)) || moment(new Date())).clone().local().daysInMonth()),
    rooms: options.rooms || [],
    allowInvalidActions: options.allowInvalidActions || false,
    assistedMovement: options.assistedMovement || false,
    endOfWeek: options.endOfWeek || 6,
    divideRoomsByCapacity: options.divideRoomsByCapacity || false,
    currencySymbol: options.currencySymbol || '€'
  };

  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar][init] Invalid Room definiton!");
  }

  /** Internal Values **/
  this._pricelist = pricelist || [];
  this._reservations = [];
  this.isNRerservation = true;
  this.tableCreated = false;
  this.cellSelection = {start:false, end:false, current:false};
  this.numRooms = this.options.rooms.length;
  /** Constants **/
  this.ACTION = { NONE: -1, MOVE_ALL: 0, MOVE_LEFT: 1, MOVE_RIGHT: 2 };

  /***/
  this._reset_action_reservation();
  if (!this._create()) {
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
      this.options.startDate = date.local().subtract('1','d').utc();
    } else if (typeof date === 'string'){
      this.options.startDate = HotelCalendar.toMomentUTC(date).local().subtract('1','d').utc();
    } else {
      console.warn("[Hotel Calendar][setStartDate] Invalid date format!");
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

  //==== RESERVATIONS
  clearReservationDivs: function(/*Boolean*/onlyUnused) {
    var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
    for (var r of reservs) {
      if ((onlyUnused && r.unusedZone) || !onlyUnused) {
    	this.e.removeChild(r);
      }
    }
  },

  getReservations: function(/*HReservation*/ignoreThis) {
    return _.reject(this._reservations, function(item){ return item===ignoreThis; });
  },

  getReservation: function(/*Int*/id) {
    return _.find(this._reservations, {'id': +id});
  },

  getReservationDiv: function(/*HReservationObject*/reservationObj) {
    var reservDiv = this.e.querySelector(`.hcal-reservation[data-hcal-reservation-obj-id='${reservationObj.id}']`);
    return reservDiv;
  },

  setReservations: function(/*List*/reservations) {
    var ids = _.pluck(this._reservations, 'id');
    for (var id of ids) {
      this.removeReservation(id, true);
    }
    this._reservations = [];
    this.addReservations(reservations);
  },

  addReservations: function(/*List*/reservations, /*Boolean*/noUnusedZones) {
    if (reservations.length > 0 && !(reservations[0] instanceof HReservation)) {
      console.warn("[HotelCalendar][setReservations] Invalid Reservation definition!");
    } else {
      // Merge
      for (var reserv of reservations) {
    	var index =  _.findKey(this._reservations, {'id': reserv.id});
        if (index) {
          this._reservations[index] = reserv;
        } else {
          this._reservations.push(reserv);
          index = this._reservations.length - 1;
        }

        var divRes = this.getReservationDiv(reserv);
        if (divRes) {
          divRes.innerText = reserv.title;
          // this._updateDivReservation(divRes, limits);
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
            // this._updateDivReservation(divRes, limits);
            this.edivr.appendChild(divRes);

            if (reserv.readOnly) {
              divRes.classList.add('hcal-reservation-readonly');
            }
            if (reserv.unusedZone) {
            	divRes.classList.add('hcal-unused-zone');
            } else {
            	this._assignReservationsEvents([divRes]);
            }
          }
        }
      }

      this.isNRerservation = true;
      this._updateReservations();
	  if (!noUnusedZones && this.options.divideRoomsByCapacity) {
      	this._updateUnusedZones();
      }
    }
  },

  removeReservation: function(/*Int*/reservationID, /*Boolean?*/noupdate) {
    var reserv = _.find(this._reservations, {'id': +reservationID});
    if (reserv) {
      var resDiv = this.getReservationDiv(reserv);
      if (resDiv) {
        resDiv.parentNode.removeChild(resDiv);
      }
      this._reservations = _.without(this._reservations, reserv);
      this.isNRerservation = true;
      if (!noupdate) {
        this._updateReservations();
        if (this.options.divideRoomsByCapacity) {
        	this._updateUnusedZones();
        }
      }
    }
  },

  getReservationsByDay: function(/*String,MomentObject*/day, /*Bool*/noStrict, /*Int?*/nroom, /*Int?*/nbed, /*HReservation?*/ignoreThis) {
    var oday = day;
	var day = HotelCalendar.toMomentUTC(day);
    if (!day) {
    	//console.log(oday);
        return false;
    }

    var stored_reservs = this.getReservations(ignoreThis);

    var reservs = [];
    for (var r of stored_reservs) {
      if (noStrict) {
    	  if ((day.isBetween(r.startDate, r.endDate.clone().startOf('day')) || day.isSame(r.startDate.clone().startOf('day')))
    	    && !day.isSame(r.endDate)
	        && (typeof nroom === 'undefined' || r.room.number == nroom)
	        && (typeof nbed === 'undefined' || r.beds_.includes(nbed))) {
	        reservs.push(r);
	      }
      } else {
		  if ((day.isBetween(r.startDate, r.endDate) || (day.isSame(r.startDate) || day.isSame(r.endDate)))
	        && (typeof nroom === 'undefined' || r.room.number == nroom)
	        && (typeof nbed === 'undefined' || r.beds_.includes(nbed))) {
	        reservs.push(r);
	      }
      }
    }

    return reservs;
  },

  getReservationCellLimits: function(/*HReservationObject*/reservation, /*Int?*/nbed, /*Bool?*/notCheck) {
    var limits = new HLimit();
    if (!reservation.startDate || !reservation.endDate) {
    	return limits;
    }

    var bedNum = 0;
    if (typeof nbed === 'undefined') {
      bedNum = (reservation.beds_&&reservation.beds_.length)?reservation.beds_[0]:0;
    } else {
      bedNum = nbed;
    }

    var diff_date = this.getDateDiffDays(reservation.startDate, reservation.endDate);
    var rpersons = (reservation.room.shared || this.options.divideRoomsByCapacity)?reservation.room.capacity:1;
    var cellFound = false;
    var cellStartType = '';
    var cellEndType = '';

    // Search Initial Cell
    var cell = this.getCell(reservation.startDate.clone().local().startOf('day'),
                            reservation.room.type,
                            reservation.room.number,
                            bedNum);
    if (!cell) {
      var date = reservation.startDate.clone().local().startOf('day');
      for (var i=0; i<=diff_date; i++) {
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
    if ((reservation.room.shared || this.options.divideRoomsByCapacity) && reservPersons > 1 && bedNum+reservPersons <= rpersons) {
      bedNum += reservPersons-1;
    }

    // Search End Cell
    var cell = this.getCell(reservation.endDate.clone().local().endOf('day'),
                            reservation.room.type,
                            reservation.room.number,
                            bedNum);
    if (!cell) {
      var date = reservation.endDate.clone().local().endOf('day');
      for (var i=0; i<=diff_date; i++) {
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
      var diff_date = this.getDateDiffDays(limitLeftDate, limitRightDate);
      var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
      var parentRow = this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`);
      for (var i=0; i<=diff_date; i++) {
    	var ndate = HotelCalendar.toMoment(parentRow.dataset.hcalDate).add(i, 'd').utc();
    	if (i === 0) {
    	  // hours are forced because no one cares about them
    	  ndate = reservation.startDate.clone().set({'hour': 12, 'minute': 0, 'second': 0});
    	}
    	if (i === diff_date) {
    	  // hours are forced because no one cares about them
    	  ndate = reservation.endDate.clone().set({'hour': 10, 'minute': 0, 'second': 0});
      	}
        for (var b=0; b<=numBeds; b++) {
          var reservs = this.getReservationsByDay(ndate, false, reservation.room.number, +limits.left.dataset.hcalBedNum+b, reservation);
          reservs = _.reject(reservs, function(item){ return item===reservation; });
          if (reservs.length) {
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
    for (var elm of elms) {
      var parentRow = this.$base.querySelector(`#${elm.dataset.hcalParentRow}`);
      if (parentRow) {
        var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
        if (room && room.type == type && room.number == number) {
          return elm;
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
    var diff_date = this.getDateDiffDays(start_date, end_date);

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
    return _.filter(reservs, function(item){ return item.room && item.room.type === room_type && !item.unusedZone; });
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
      var price_input = this.edtable.querySelector('#'+this._sanitizeId(`CELL_PRICE_${room.price[2]}_${room.price[1]}_${day.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
      if (r.unusedZone) {
    	continue;
      }
      num_rooms -= (r.room && r.room.shared)?r.getTotalPersons():1;
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
      if (r.unusedZone) {
    	continue;
      }
      num_rooms -= (r.room && r.room.shared)?r.getTotalPersons():1;
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
  _reset_action_reservation: function() {
    this.reservationAction = {
      action: this.ACTION.NONE,
      reservation: null,
      oldReservationObj: null,
      newReservationObj: null
    };
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
  _create: function() {
	while (this.e.hasChildNodes()) {
		this.e.removeChild(this.e.lastChild);
	}

    if (this.tableCreated) {
      console.warn("[Hotel Calendar] Already created!");
      return false;
    }

    // Reservations Table
    this.edivrh = document.createElement("div");
    this.edivrh.classList.add('table-reservations-header');
    this.e.appendChild(this.edivrh);
    this.etableHeader = document.createElement("table");
    this.etableHeader.classList.add('hcal-table');
    this.etableHeader.classList.add('noselect');
    this.edivrh.appendChild(this.etableHeader);
    this.edivr = document.createElement("div");
    this.edivr.classList.add('table-reservations');
    this.e.appendChild(this.edivr);
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-table');
    this.etable.classList.add('noselect');
    this.edivr.appendChild(this.etable);
    // Detail Calcs Table
    this.edivch = document.createElement("div");
    this.edivch.classList.add('table-calcs-header');
    this.e.appendChild(this.edivch);
    this.edtableHeader = document.createElement("table");
    this.edtableHeader.classList.add('hcal-table');
    this.edtableHeader.classList.add('noselect');
    this.edivch.appendChild(this.edtableHeader);
    this.edivc = document.createElement("div");
    this.edivc.classList.add('table-calcs');
    this.e.appendChild(this.edivc);
    this.edtable = document.createElement("table");
    this.edtable.classList.add('hcal-table');
    this.edtable.classList.add('noselect');
    this.edivc.appendChild(this.edtable);

    this._updateView();
    this.tableCreated = true;

    return true;
  },

  _generateTableDay: function(/*HTMLObject*/parentCell) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var roomNumber = $this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`).dataset.hcalRoomObjId;
    var room = $this.getRoom(roomNumber);
    var num = ((room.shared || this.options.divideRoomsByCapacity)?room.capacity:1);
    for (var i=0; i<num; i++) {
      row = table.insertRow();
      cell = row.insertCell();
      cell.dataset.hcalParentRow = parentCell.dataset.hcalParentRow;
      cell.dataset.hcalParentCell = parentCell.getAttribute('id');
      cell.dataset.hcalBedNum = i;
      cell.addEventListener('mouseenter', function(ev){
        var date_cell = HotelCalendar.toMoment($this.etable.querySelector(`#${this.dataset.hcalParentCell}`).dataset.hcalDate);
        if ($this._isLeftButtonPressed(ev)) {
          var reserv = null;
          var toRoom = undefined;
          var needUpdate = false;
          if (!$this.reservationAction.reservation) {
            if ($this.cellSelection.start && $this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow) {
              $this.cellSelection.current = this;
            }
            $this._updateCellSelection();
          } else if ($this.reservationAction.action == $this.ACTION.MOVE_RIGHT) {
            reserv = $this.getReservation($this.reservationAction.reservation.dataset.hcalReservationObjId);
            if (reserv.fixDays) {
              $this._reset_action_reservation();
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
              $this._reset_action_reservation();
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
            var diff_date = $this.getDateDiffDays(reserv.startDate, reserv.endDate);
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
                if (lr.unusedZone) {
                  reservationDiv.style.visibility = 'hidden';
                  continue;
                }
                var limits = $this.getReservationCellLimits(
                  lr,
                  lr===reserv?toRoom:undefined,
                  !$this.options.assistedMovement);
                $this._updateDivReservation(reservationDiv, limits);

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
        $this._updateCellSelection();
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

  _createTableReservationDays: function() {
    var $this = this;
    this.etableHeader.innerHTML = "";
    this.etable.innerHTML = "";
    /** TABLE HEADER **/
    var thead = this.etableHeader.createTHead();
    var row = thead.insertRow();
    var row_init = row;
    // Current Date
    var cell = row.insertCell();
    cell.setAttribute('rowspan', 2);
    cell.setAttribute('colspan', 3);

    // Render Next Days
    row = thead.insertRow();
    var months = { };
    var cur_month = this.options.startDate.clone().local().format("MMMM");
    months[cur_month] = {};
    months[cur_month].year = this.options.startDate.clone().local().format("YYYY");
    months[cur_month].colspan = 0;
    var now = moment();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd_local.format('D')}<br/>${dd_local.format('ddd')}`;
      cell.setAttribute('title', dd_local.format('dddd'))
      var day = +dd_local.format('D');
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
        cur_month = dd_local.format('MMMM');
        months[cur_month] = {};
        months[cur_month].year = dd.format('YYYY');
        months[cur_month].colspan = 0;
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') == this.options.endOfWeek) {
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
      row.setAttribute('id', $this._sanitizeId(`ROW_${itemRoom.number}_${itemRoom.type}_${indexRoom}`));
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      cell = row.insertCell();
      cell.textContent = itemRoom.number;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.setAttribute('colspan', '2');
      cell = row.insertCell();
      cell.textContent = itemRoom.type;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-flat');
      for (var i=0; i<=$this.options.days; i++) {
    	var dd = $this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
        var dd_local = dd.clone().local();
        cell = row.insertCell();
        cell.setAttribute('id', $this._sanitizeId(`${itemRoom.type}_${itemRoom.number}_${indexRoom}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
        // Generate Interactive Table
        cell.appendChild($this._generateTableDay(cell));
        //cell.innerHTML = dd.format("DD");
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        } else if (dd_local.format('e') == $this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
    });
  },

  _createTableDetailDays: function() {
    var $this = this;
    this.edtableHeader.innerHTML = "";
    this.edtable.innerHTML = "";
    /** DETAIL DAYS HEADER **/
    var now = moment();
    var thead = this.edtableHeader.createTHead();
    var row = thead.insertRow();
    var cell = row.insertCell();
    cell.setAttribute('colspan', 3);
    //cell.setAttribute('class', 'col-xs-1 col-lg-1');
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd_local.format('D')}<br/>${dd_local.format('ddd')}`;
      cell.setAttribute('title', dd_local.format("dddd"))
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') == this.options.endOfWeek) {
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
        row.setAttribute('id', this._sanitizeId(`ROW_DETAIL_FREE_TYPE_${rt}`));
        row.dataset.hcalRoomType = rt;
        row.classList.add('hcal-row-detail-room-free-type-group-item');
        cell = row.insertCell();
        cell.textContent = rt;
        cell.classList.add('hcal-cell-detail-room-free-type-group-item');
        cell.classList.add('btn-hcal');
        cell.classList.add('btn-hcal-flat');
        cell.setAttribute("colspan", "3");
        for (var i=0; i<=this.options.days; i++) {
          var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
          var dd_local = dd.clone().local();
          cell = row.insertCell();
          cell.setAttribute('id', this._sanitizeId(`CELL_FREE_${rt}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
          cell.dataset.hcalParentRow = row.getAttribute('id');
          cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
          cell.textContent = '0';
          var day = +dd_local.format("D");
          if (day == 1) {
            cell.classList.add('hcal-cell-start-month');
          }
          if (dd_local.isSame(now, 'day')) {
            cell.classList.add('hcal-cell-current-day');
          } else if (dd_local.format('e') == $this.options.endOfWeek) {
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
    cell.setAttribute("colspan", "3");
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_TOTAL_FREE_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.textContent = '0';
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') == this.options.endOfWeek) {
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
    cell.setAttribute("colspan", "3");
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_PERC_OCCUP_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.textContent = '0';
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') == this.options.endOfWeek) {
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
          row.setAttribute('id', this._sanitizeId(`ROW_DETAIL_PRICE_ROOM_${key}_${listitem.room}`));
          row.dataset.hcalPricelist = key;
          row.dataset.hcalRoom = listitem.room
          row.classList.add('hcal-row-detail-room-price-group-item');
          cell = row.insertCell();
          cell.innerHTML = "<marquee behavior='alternate' scrollamount='1' scrolldelay='100'>"+listitem.title + ' ' + this.options.currencySymbol+ '</marquee>';
          cell.classList.add('hcal-cell-detail-room-group-item');
          cell.classList.add('btn-hcal');
          cell.classList.add('btn-hcal-flat');
          cell.setAttribute("colspan", "3");
          for (var i=0; i<=$this.options.days; i++) {
        	var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
            var dd_local = dd.clone().local();
            cell = row.insertCell();
            cell.setAttribute('id', this._sanitizeId(`CELL_PRICE_${key}_${listitem.room}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
            cell.classList.add('hcal-cell-detail-room-price-group-item-day');
            cell.dataset.hcalParentRow = row.getAttribute('id');
            cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
            var day = +dd_local.format("D");
            if (day == 1) {
              cell.classList.add('hcal-cell-start-month');
            }
            if (dd_local.isSame(now, 'day')) {
              cell.classList.add('hcal-cell-current-day');
            } else if (dd_local.format('e') == $this.options.endOfWeek) {
              cell.classList.add('hcal-cell-end-week');
            }

            var dd_fmrt = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
            cell.textContent = _.has(listitem['days'], dd_fmrt)?listitem['days'][dd_fmrt]:'...';
          }
        }
      }
    }
  },

  //==== UPDATE FUNCTIONS
  _updateView: function() {
    this._createTableReservationDays();
    this._createTableDetailDays();

    this._updateReservations();
    if (this.options.divideRoomsByCapacity) {
    	this._updateUnusedZones();
    }
    this._updateCellSelection();
  },

  _updateHighlightInvalidZones: function(/*HReservation*/reserv) {
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
      var diff_date = this.getDateDiffDays(limitLeftDateMoment, limitRightDateMoment);
      var date = limitLeftDateMoment.clone().startOf('day');
      var selector = [];
      for (var i=0; i<=diff_date; i++) {
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
  _updateCellSelection: function() {
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
          if (this._pricelist) {
        	var parentRow = this.$base.querySelector(`#${c.dataset.hcalParentRow}`);
            var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${c.dataset.hcalParentCell}`).dataset.hcalDate);
            var room_price = this.getRoomPrice(parentRow.dataset.hcalRoomObjId, date_cell);
            var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
            if (c === cells[0] || !date_cell.isSame(limitRightDate, 'day')) {
	            c.textContent = room_price + ' ' + this.options.currencySymbol;
	            if (!room.shared && c.dataset.hcalBedNum > limits.left.dataset.hcalBedNum) {
	              c.style.color = 'lightgray';
	            }
	            else {
	              c.style.color = 'black';
	              total_price += room_price;
	            }
            }
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

  _resetCellSelection: function() {
    this.cellSelection = { current: false, end: false, start: false };
  },

  //==== RESERVATIONS
  _updateDivReservation: function(/*HTMLObject*/divRes, /*HLimitObject*/limits) {
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
    var rgb = this._hexToRGB(`0x${reserv.color.substr(1)}`);
    var invColor = this._getInverseColor(rgb[0]/255, rgb[1]/255, rgb[2]/255);
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

      var index = _.findKey(this._reservations, {'id': reservationObj.id});
      delete this._reservations[index];
      this._reservations[index] = newReservationObj;
      reservationDiv.dataset.hcalReservationObjId = newReservationObj.id;
      var limits = this.getReservationCellLimits(newReservationObj);
      this._updateDivReservation(reservationDiv, limits);

      var linkedReservations = this.getLinkedReservations(newReservationObj);
      for (var lr of linkedReservations) {
        lr.startDate = newReservationObj.startDate.clone();
        lr.endDate = newReservationObj.endDate.clone();

        var reservationDiv = this.getReservationDiv(lr);
        if (reservationDiv) {
          var limits = this.getReservationCellLimits(lr);
          this._updateDivReservation(reservationDiv, limits);
        }
      }
      this._updateReservationOccupation();
  },

  setDetailPrice: function(/*String*/room_type, /*String*/date, /*Float*/price) {
    var dd = HotelCalendar.toMomentUTC(date);
    var selector = this._sanitizeId(`#CELL_PRICE_${room_type}_${dd.local().format(HotelCalendar.DATE_FORMAT_SHORT_)}`);
    var cell_input = this.edtable.querySelector(`${selector} input`);
    cell_input.value = price;
  },

  getLinkedReservations: function(/*HReservationObject*/reservationObj) {
    return _.reject(this._reservations, function(item){ return item === reservationObj || item.linkedId !== reservationObj.id; });
  },

  _updateReservations: function() {
      var $this = this;

      var errors = [];
      this._reservations.forEach(function(itemReserv, indexReserv){
        var limits = $this.getReservationCellLimits(itemReserv);

        // Fill
        if (limits.isValid()) {
          var divRes = $this.getReservationDiv(itemReserv);
          $this._updateDivReservation(divRes, limits);
        } else {
          console.warn(`[Hotel Calendar][updateReservations_] Can't place reservation ID@${itemReserv.id}`);
          errors.push(itemReserv.id);
        }
      });

      // Delete Reservations with errors
      for (var reservID of errors) {
        this.removeReservation(reservID, true);
      }

      //this._assignReservationsEvents();
      this._updateReservationOccupation();
      //this._updatePriceList();

//        if (errors.length && this.isNRerservation) {
//            alert("[Hotel Calendar]\nWARNING: Can't show all reservations!\n\nSee debugger for more details.");
//        }
      this.isNRerservation = false;
  },

  _assignReservationsEvents: function(reservDivs) {
    var $this = this;
    reservDivs = reservDivs || this.e.querySelectorAll('div.hcal-reservation');
    for (var rdiv of reservDivs) {
      var bounds = rdiv.getBoundingClientRect();
      rdiv.addEventListener('mousemove', function(ev){
        var posAction = $this._getRerservationPositionAction(this, ev.layerX, ev.layerY);
        this.style.cursor = (posAction == $this.ACTION.MOVE_LEFT || posAction == $this.ACTION.MOVE_RIGHT)?'col-resize':'pointer';
      }, false);
      rdiv.addEventListener('mousedown', function(ev){
        if (!$this.reservationAction.reservation && $this._isLeftButtonPressed(ev)) {
          $this.reservationAction = {
            action: $this._getRerservationPositionAction(this, ev.layerX, ev.layerY),
            reservation: this
          };

          var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
          $this._updateHighlightInvalidZones(reserv);
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

          var otherReservs = _.difference($this._reservations, linkedReservations);
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

  _getRerservationPositionAction: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
    var bounds = elm.getBoundingClientRect();
    if (posX <= 5) { return this.ACTION.MOVE_LEFT; }
    else if (posX >= bounds.width-10) { return this.ACTION.MOVE_RIGHT; }
    return this.ACTION.MOVE_ALL;
  },

  _cleanAllUnusedZones: function() {
	  var unusedZones = this.e.querySelectorAll('div.hcal-unused-zone');
	  for (var uz of unusedZones) {
		  this.removeReservation(uz.dataset.hcalReservationObjId, true);
	  }
  },

  _updateUnusedZones: function() {
    if (this.options.divideRoomsByCapacity) {
    	this._cleanAllUnusedZones();
    }

    var unused_id = 0;
    var reservs = this.getReservations();
    var nreservs = [];
    for (var itemReserv of reservs) {
    	if (itemReserv.unusedZone) {
    		continue;
    	}
		var numBeds = itemReserv.getTotalPersons();
	  	for (var e=numBeds; e<itemReserv.room.capacity; e++) {
	  		nreservs.push(new HReservation(
	  			--unused_id,
	  			itemReserv.room,
	            'Unused Zone',
	            1,
	            0,
	            itemReserv.startDate.clone(),
	            itemReserv.endDate.clone(),
	            'black',
	            true,
	            true,
	            true,
	            true,
	            itemReserv.id
	  		));
	  	}
    }
  	this.addReservations(nreservs, true);
  },

  _updateReservationOccupation: function() {
    var cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-type-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityByType(parentRow.dataset.hcalRoomType); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTypeReservations(cell_date, parentRow.dataset.hcalRoomType);
      cell.innerText = occup;
      cell.style.backgroundColor = this._generateColor(occup, num_rooms, 0.35, true, true);
    }

    cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-total-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityTotal(); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTotalReservations(cell_date);
      cell.innerText = occup;
      cell.style.backgroundColor = this._generateColor(occup, num_rooms, 0.35, true, true);
    }

    cells = this.edtable.querySelectorAll('td.hcal-cell-detail-room-perc-occup-group-item-day');
    for (var cell of cells) {
      var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
      var cell_date = cell.dataset.hcalDate;
      var num_rooms = this.getRoomsCapacityTotal(); // FIXME: Too expensive, hard search!!
      var occup = this.calcDayRoomTotalReservations(cell_date);
      var perc = 100.0 - (occup * 100.0 / num_rooms);
      cell.innerText = perc.toFixed(0);
      cell.style.backgroundColor = this._generateColor(perc, 100.0, 0.35, false, true);
    }
  },

  //==== PRICELIST
  setPricelist: function(/*List*/pricelist) {
    this._pricelist = pricelist;
    this._updatePriceList();
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
    this._updatePriceList();
  },

  getPricelist: function(/*Int*/pricelist_id) {
    return this._pricelist[pricelist_id];
  },

  _updatePriceList: function() {
    var keys = _.keys(this._pricelist);
    for (var k of keys) {
      var pr = this._pricelist[k];
      for (var pr_item of pr) {
        var pr_keys = _.keys(pr_item['days']);
        for (var prk of pr_keys) {
          var dd = HotelCalendar.toMomentUTC(prk, HotelCalendar.DATE_FORMAT_SHORT_);
          var price = pr_item['days'][prk];
          var cell = this.edtable.querySelector('#'+this._sanitizeId(`CELL_PRICE_${k}_${pr_item['room']}_${dd.local().startOf('day').utc().format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          if (cell) {
            cell.textContent = price;
          }
        }
      }
    }
  },

  //==== HELPER FUNCTIONS
  getDateDiffDays: function(/*MomentObject*/start, /*MomentObject*/end) {
	  return end.clone().startOf('day').diff(start.clone().startOf('day'), 'days');
  },

  _sanitizeId: function(/*String*/str) {
    return str.replace(/[\/\s\+\-]/g, '_');
  },

  _isLeftButtonPressed: function(/*EventObject*/evt) {
    evt = evt || window.event;
    return ("buttons" in evt)?(evt.buttons === 1):(evt.which || evt.button);
  },

  toAbbreviation: function(/*String*/word, /*Int*/max) {
    return word.replace(/[aeiouáéíóúäëïöü]/gi,'').toUpperCase().substr(0, max || 3);
  },

  checkReservationPlace: function(/*HReservationObject*/reservationObj) {
    var persons = reservationObj.getTotalPersons();
    if (((reservationObj.room.shared || this.options.divideRoomsByCapacity) && reservationObj.beds_.length < persons)
      || (!(reservationObj.room.shared || this.options.divideRoomsByCapacity) && persons > reservationObj.room.capacity)) {
      return false;
    }

    var reservs = this.getReservations(reservationObj);
    for (var r of reservs) {
      if (r.unusedZone) {
    	continue;
      }
      if ((reservationObj.room.number == r.room.number)
        && (_.difference(reservationObj.beds_, r.beds_).length != reservationObj.beds_.length
        		|| this.options.divideRoomsByCapacity)
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
        this._updateHighlightInvalidZones();

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
            this.swapReservation(this.reservationAction.newReservationObj, this.reservationAction.oldReservationObj);
          } else {
            this.e.dispatchEvent(new CustomEvent(
              'hcalOnChangeReservation',
              { 'detail': {
                  'oldReserv':this.reservationAction.oldReservationObj,
                  'newReserv':this.reservationAction.newReservationObj
                }
              }));
            this._updateReservationOccupation();
          }
          reservDiv.classList.remove('hcal-reservation-invalid');
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
        this._reset_action_reservation();
    }
    this._resetCellSelection();
    this._updateCellSelection();
  },

  onMainResize: function(/*EventObject*/ev) {
    this._updateReservations();
    if (this.options.divideRoomsByCapacity) {
    	this._updateUnusedZones();
    }
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
  _hueToRgb: function(/*Int*/v1, /*Int*/v2, /*Int*/h) {
    if (h<0.0) { h+=1; }
    if (h>1.0) { h-=1; }
    if ((6.0*h) < 1.0) { return v1+(v2-v1)*6.0*h; }
    if ((2.0*h) < 1.0) { return v2; }
    if ((3.0*h) < 2.0) { return v1+(v2-v1)*((2.0/3.0)-h)*6.0; }
    return v1;
  },

  _hslToRgb: function(/*Int*/h, /*Int*/s, /*Int*/l) {
    if (s == 0.0) {
      return [l,l,l];
    }
    var v2 = l<0.5?l*(1.0+s):(l+s)-(s*l);
    var v1 = 2.0*l-v2;
    return [
      this._hueToRgb(v1,v2,h+(1.0/3.0)),
      this._hueToRgb(v1,v2,h),
      this._hueToRgb(v1,v2,h-(1.0/3.0))];
  },

  _RGBToHex: function(/*Int*/r, /*Int*/g, /*Int*/b){
    var bin = r << 16 | g << 8 | b;
    return (function(h){
      return new Array(7-h.length).join("0")+h;
    })(bin.toString(16).toUpperCase());
  },

  _hexToRGB: function(/*Int*/hex){
    var r = hex >> 16;
    var g = hex >> 8 & 0xFF;
    var b = hex & 0xFF;
    return [r,g,b];
  },

  _getInverseColor: function(/*Int*/r, /*Int*/g, /*Int*/b) {
      //return this._hslToRgb(hsl[0], hsl[1], hsl[2]);
    return [1.0-r, 1.0-g, 1.0-b];
  },

  _generateColor: function(/*Int*/value, /*Int*/max, /*Int*/offset, /*Bool*/reverse, /*Bool*/strmode) {
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
    rgb = this._hslToRgb(((max-value)*offset)/max, 1.0, 0.5);
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

  //debugger;
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

  //debugger;
  console.warn('[Hotel Calendar][toMomentUTC] Invalid date format!');
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
                        /*String?*/color, /*Boolean?*/readOnly, /*Boolean?*/fixDays, /*Boolean?*/fixRooms,
                        /*Boolean?*/unusedZone, /*Int?*/linkedId) {
  if (typeof room === 'undefined') {
    delete this;
    console.warn("[Hotel Calendar][HReservation] room can't be empty!");
    return;
  }

  this.id = id;
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
  this.unusedZone = unusedZone || false;
  this.linkedId = linkedId || -1;

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

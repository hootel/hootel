/* global _, moment */
'use strict';
/*
 * Hotel Calendar JS - 2017-2018
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 *
 * Dependencies:
 *     - moment
 *     - underscore
 *     - awesomeicons !shit
 *     - bootstrap !shit
 *     - datetimepicker !shit
 */


function HotelCalendar(/*String*/querySelector, /*Dictionary*/options, /*List*/pricelist, /*restrictions*/restrictions, /*HTMLObject?*/_base) {
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
      Version: '0.2',
      Author: "Alexandre Díaz",
      Created: "20/04/2017",
      Updated: "11/04/2018"
    };
  }

  /** Options **/
  options = options || {};
  this.options = {
    startDate: ((options.startDate && HotelCalendar.toMomentUTC(options.startDate)) || moment(new Date()).utc()).subtract('1', 'd'),
    days: (options.days || ((options.startDate && HotelCalendar.toMomentUTC(options.startDate)) || moment(new Date())).clone().local().daysInMonth()),
    rooms: options.rooms || [],
    allowInvalidActions: options.allowInvalidActions || false,
    assistedMovement: options.assistedMovement || false,
    endOfWeek: options.endOfWeek || 6,
    endOfWeekOffset: options.endOfWeekOffset || 0,
    divideRoomsByCapacity: options.divideRoomsByCapacity || false,
    currencySymbol: options.currencySymbol || '€',
    showPricelist: options.showPricelist || false,
    showAvailability: options.showAvailability || false,
    showNumRooms: options.showNumRooms || 0,
    paginatorStepsMin: options.paginatorAdv || 1,
    paginatorStepsMax: options.paginatorAdv || 15,
  };

  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar][init] Invalid Room definiton!");
  }

  /** Internal Values **/
  this._pricelist = pricelist || []; // Store Prices
  this._pricelist_id = -1;  // Store Price Plan ID (Because can be edited)
  this._restrictions = restrictions || {}; // Store Restrictions
  this._reservations = [];  // Store Reservations
  this._reservationsMap = {}; // Store Reservations Mapped by Room for Search Purposes
  this._modeSwap = HotelCalendar.MODE.NONE; // Store Swap Mode
  this._endDate = this.options.startDate.clone().add(this.options.days, 'd'); // Store End Calendar Day
  this._tableCreated = false; // Store Flag to Know Calendar Creation
  this._cellSelection = {start:false, end:false, current:false}; // Store Info About Selected Cells
  this._lazyModeReservationsSelection = false; // Store Info About Timer for Selection Action
  this._domains = {}; // Store domains for filter rooms & reservations

  /***/
  this._reset_action_reservation();
  if (!this._create()) {
    return false;
  }


  /** Main Events **/
  document.addEventListener('mouseup', this.onMainMouseUp.bind(this), false);
  document.addEventListener('touchend', this.onMainMouseUp.bind(this), false);
  document.addEventListener('keyup', this.onMainKeyUp.bind(this), false);
  document.addEventListener('keydown', this.onMainKeyDown.bind(this), false);
  window.addEventListener('resize', _.debounce(this.onMainResize.bind(this), 300), false);

  return this;
}

HotelCalendar.prototype = {
  /** PUBLIC MEMBERS **/
  addEventListener: function(/*String*/event, /*Function*/callback) {
    this.e.addEventListener(event, callback);
  },

  //==== CALENDAR
  setStartDate: function(/*String,MomentObject*/date, /*Int?*/days, /*Bool*/fullUpdate, /*Functions*/callback) {
    if (moment.isMoment(date)) {
      this.options.startDate = date.subtract('1','d');
    } else if (typeof date === 'string'){
      this.options.startDate = HotelCalendar.toMomentUTC(date).subtract('1','d');
    } else {
      console.warn("[Hotel Calendar][setStartDate] Invalid date format!");
      return;
    }

    if (typeof days !== 'undefined') {
      this.options.days = days;
    }

    this._endDate = this.options.startDate.clone().add(this.options.days, 'd');

    /*this.e.dispatchEvent(new CustomEvent(
            'hcOnChangeDate',
            {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));*/
    this._updateView(!fullUpdate, callback);
  },

  getOptions: function(/*String?*/key) {
    if (typeof key !== 'undefined') {
      return this.options[key];
    }
    return this.options;
  },

  setSwapMode: function(/*Int*/mode) {
    if (mode !== this._modeSwap) {
      this._modeSwap = mode;
      if (this._modeSwap === HotelCalendar.MODE.NONE) {
        this._dispatchSwapReservations();
        this._reset_action_reservation();
      }

      this._updateHighlightSwapReservations();
    }
  },

  getSwapMode: function() {
    return this._modeSwap;
  },

  //==== DOMAINS
  setDomain: function(/*Int*/section, /*Array*/domain) {
    if (this._domains[section] !== domain) {
      this._domains[section] = domain;
      if (section === HotelCalendar.DOMAIN.RESERVATIONS) {
        this._filterReservations();
      } else if (section === HotelCalendar.DOMAIN.ROOMS) {
        this._filterRooms();
      }
    }
  },

  getDomain: function(/*Int*/section) {
    return this._domains[section];
  },

  //==== RESERVATIONS
  _filterReservations: function() {
    for (var r of this._reservations) {
      r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.RESERVATIONS]);
      this._updateReservation(r, true);
    }

    //_.defer(function(){ this._updateReservationOccupation() }.bind(this));
  },

  getReservationAction: function() {
    return this.reservationAction;
  },

  getReservation: function(/*Int,String*/id) {
    return _.find(this._reservations, function(item){ return item.id == id; });
  },

  // getReservationDiv: function(/*HReservationObject*/reservationObj) {
  //   var reservDiv = this.e.querySelector(`div.hcal-reservation[data-hcal-reservation-obj-id='${reservationObj.id}']`);
  //   return reservDiv;
  // },

  setReservations: function(/*List*/reservations) {
    for (var reservation of this._reservations) {
      this.removeReservation(reservation);
    }

    this._reservations = [];
    this.addReservations(reservations);
  },

  addReservations: function(/*List*/reservations, /*Bool*/forced) {
    if (!reservations || reservations.length === 0) {
      return;
    }

    if (reservations.length > 0 && !(reservations[0] instanceof HReservation)) {
      console.warn("[HotelCalendar][addReservations] Invalid Reservation definition!");
    } else {
      // Merge
      var uzr = [];
      for (var r of reservations) {
        var rindex = !forced?_.findKey(this._reservations, {'id': r.id}):false;
        if (rindex) {
          r._html = this._reservations[rindex]._html;
          this._reservations[rindex] = r;
          this._cleanUnusedZones(r);
        } else {
          this._reservations.push(r);
        }
      }

      // Create & Render New Reservations
      _.defer(function(reservs){
        var unusedZones = this._createUnusedZones(reservs);
        // Add Unused Zones
        this._reservations = this._reservations.concat(unusedZones);
        // Create Map
        this._updateReservationsMap();

        reservs = reservs.concat(unusedZones);
        for (var r of reservs) {
          r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.RESERVATIONS]);
          this._calcReservationCellLimits(r);
          if (r._html) {
            r._html.innerText = r.title;
          } else {
            if (r._limits.isValid()) {
              r._html = document.createElement('div');
              r._html.dataset.hcalReservationObjId = r.id;
              r._html.classList.add('hcal-reservation');
              r._html.classList.add('noselect');
              r._html.innerText = r.title;
              this.edivr.appendChild(r._html);

              if (r.unusedZone) {
              	r._html.classList.add('hcal-unused-zone');
              } else {
              	this._assignReservationsEvents([r._html]);
              }
            }
          }
          this._updateReservation(r);
        }
      }.bind(this), reservations);

      _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
    }
  },

  removeReservation: function(/*Int/HReservationObject*/reservation) {
    var reserv = reservation;
    if (!(reserv instanceof HReservation)) {
      reserv = this.getReservation(reservation);
    }
    if (reserv) {
      // Remove all related content...
      var elms = [reserv._html, this.e.querySelector(`.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`)];
      for (var elm of elms) {
        if (elm && elm.parentNode) {
          elm.parentNode.removeChild(elm);
        }
      }
      // Remove OB Row
      if (reserv.overbooking) {
        if (this.getReservationsByRoom(reserv.room).length === 1) {
          this.removeOBRoomRow(reserv);
        }
      }
      // Remove Unused Zones
      this._cleanUnusedZones(reserv);

      this._reservations = _.without(this._reservations, reserv);
      this._updateReservationsMap();
    } else {
      console.warn(`[HotelCalendar][removeReservation] Can't remove '${reservation.id}' reservation!`);
    }
  },

  getReservationsByDay: function(/*MomentObject*/day, /*Bool?*/noCheckouts, /*Bool?*/includeUnusedZones, /*Int?*/nroom, /*Int?*/nbed, /*HReservation?*/ignoreThis) {
    var inclusivity = noCheckouts?'[)':'[]';

    if (typeof nroom !== 'undefined') {
      return _.filter(this._reservationsMap[nroom], function(item){
        return day.isBetween(item.startDate, item.endDate, 'day', inclusivity) &&
                (typeof nbed === 'undefined' || item._beds.includes(nbed)) &&
                ((includeUnusedZones && item.unusedZone) || !item.unusedZone) &&
                item !== ignoreThis;
      });
    } else {
      return _.filter(this._reservations, function(item){
        return day.isBetween(item.startDate, item.endDate, 'day', inclusivity) &&
                (typeof nbed === 'undefined' || item._beds.includes(nbed)) &&
                ((includeUnusedZones && item.unusedZone) || !item.unusedZone) &&
                item !== ignoreThis;
      });
    }
  },

  getReservationsByRoom: function(/*Int,HRoomObject*/room, /*Boolean*/includeUnusedZones) {
    if (!(room instanceof HRoom)) { room = this.getRoom(room); }
    return _.filter(this._reservationsMap[room.id], function(item){
      return (includeUnusedZones || (!includeUnusedZones && !item.unusedZone));
    });
  },

  _updateReservationsMap: function() {
    this._reservationsMap = {};
    this._reservations.map(function(current){
      if (!(current.room.id in this._reservationsMap)) {
        this._reservationsMap[current.room.id] = [];
      }
      this._reservationsMap[current.room.id].push(current);
    }.bind(this));
  },

  _calcReservationCellLimits: function(/*HReservationObject*/reservation, /*Int?*/nbed, /*Bool?*/notCheck) {
    var limits = new HLimit();
    if (!reservation.startDate || !reservation.endDate) {
    	return limits;
    }

    var notFound;
    do {
      notFound = false;

      // Num of beds
      var bedNum;
      if (typeof nbed === 'undefined') {
        if (reservation._beds && reservation._beds.length) {
          bedNum = reservation._beds[0];
        } else {
          bedNum = (reservation.unusedZone)?1:0;
        }
      } else {
        bedNum = nbed;
      }

      // Search Initial Cell
      if (reservation.startDate.clone().local().isSameOrAfter(this.options.startDate, 'd')) {
        reservation._drawModes[0] = 'hard-start';
        limits.left = this.getCell(reservation.startDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }
      else {
        reservation._drawModes[0] = 'soft-start';
        limits.left = this.getCell(this.options.startDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }

      // More Beds?
      var rpersons = (reservation.room.shared || this.options.divideRoomsByCapacity)?reservation.room.capacity:1;
      var reservPersons = reservation.getTotalPersons();
      if ((reservation.room.shared || this.options.divideRoomsByCapacity) && reservPersons > 1 && bedNum+reservPersons <= rpersons) {
        bedNum += reservPersons-1;
      }

      // Search End Cell
      if (reservation.endDate.clone().local().isSameOrBefore(this._endDate, 'd')) {
        reservation._drawModes[1] = 'hard-end';
        limits.right = this.getCell(reservation.endDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }
      else {
        reservation._drawModes[1] = 'soft-end';
        limits.right = this.getCell(this._endDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }

      // Exists other reservation in the same place?
      if (!notCheck && limits.isValid()) {
        var diff_date = this.getDateDiffDays(reservation.startDate, reservation.endDate);
        var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
        var ndate = reservation.startDate.clone();
        for (var i=0; i<diff_date; ++i) {
          for (var b=0; b<=numBeds; ++b) {
            var reservs = this.getReservationsByDay(ndate, true, true, reservation.room.id, +limits.left.dataset.hcalBedNum+b, reservation);
            if (reservs.length) {
              notFound = true;
              nbed = nbed?nbed+1:+limits.left.dataset.hcalBedNum+b+1;
              break;
            }
          }
          if (notFound) { break; }
          ndate.add(1, 'd');
        }
      }
    } while (notFound && nbed <= reservation.room.capacity);

    reservation._limits = limits;
  },

  //==== CELLS
  getMainCell: function(/*MomentObject*/date, /*String*/type, /*String*/number) {
    return this.etable.querySelector('#'+this._sanitizeId(`${type}_${number}_${date.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
  },

  getCell: function(/*MomentObject*/date, /*HRoomObj*/room, /*Int*/bednum) {
    return this.etable.querySelector("td[data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'][data-hcal-room-obj-id='"+room.id+"'] table td[data-hcal-bed-num='"+bednum+"']");
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
      var cell = this.getCell(date, room, +limits.left.dataset.hcalBedNum+nbed);
      if (cell) {
        cells.push(cell);
      }
      for (var i=0; i<diff_date; i++) {
        cell = this.getCell(
          date.add(1, 'd'),
          room,
          +limits.left.dataset.hcalBedNum+nbed);
        if (cell) {
          cells.push(cell);
        }
      }
    }

    return cells;
  },

  //==== ROOMS
  _filterRooms: function() {
    for (var r of this.options.rooms) {
      r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.ROOMS]);
      if (r._active) {
        r._html.classList.remove('hcal-hidden');
      } else {
        r._html.classList.add('hcal-hidden');
      }
      if (r.id in this._reservationsMap) {
        for (var reserv of this._reservationsMap[r.id]) {
          this._updateReservation(reserv);
        }
      }
    }

    this._calcViewHeight();
    //_.defer(function(){ this._updateReservationOccupation() }.bind(this));
  },

  getDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    var reservs = this.getReservationsByDay(day, true);
    return _.filter(reservs, function(item){ return item.room && item.room.type === room_type && !item.unusedZone; });
  },

  getRoomsByType: function(/*String*/type) {
    return _.filter(this.options.rooms, function(item){ return item.type === type && !item.overbooking; });
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
    var rooms = _.filter(this.options.rooms, function(item){ return !item.overbooking; });
    for (var tr of rooms) {
      num_rooms += tr.shared?tr.capacity:1;
    }
    return num_rooms;
  },

  getRoomTypes: function() {
    return _.uniq(_.pluck(this.options.rooms, 'type'));
  },

  getOBRooms: function(/*Int*/parentRoomId) {
    var $this = this;
    return _.filter(this.options.rooms, function(item) {
      return (item.overbooking && +$this.parseOBRoomId(item.id)[1] === +parentRoomId);
    });
  },

  getRoom: function(/*String,Int*/id, /*Boolean?*/isOverbooking, /*Int?*/reservId) {
    if (isOverbooking) {
      return _.find(this.options.rooms, function(item){ return item.id === `${reservId}@${id}` && item.overbooking; });
    }
    return _.find(this.options.rooms, function(item){ return item.id == id; });
  },

  _insertRoomAt: function(/*HRoomObject*/roomI, /*HRoomObject*/newRoom, /*Boolean*/isAfter) {
    this.options.rooms.splice(_.indexOf(this.options.rooms, roomI)+(isAfter?1:0), 0, newRoom);
  },

  getRoomPrice: function(/*String,HRoom*/id, /*String,MomentObject*/day) {
    var day = HotelCalendar.toMoment(day);
    if (!day) {
      return 0.0;
    }

    var room = id;
    if (!(room instanceof HRoom)) {
      room = this.getRoom(id);
    }
    if (room.price[0] == 'fixed') {
      return room.price[1];
    } else if (room.price[0] == 'pricelist') {
      var pricelist = _.find(this._pricelist[this._pricelist_id], function(item){ return item.room == room.price[1]; });
      if (day.format(HotelCalendar.DATE_FORMAT_SHORT_) in pricelist['days']) {
          return pricelist['days'][day.format(HotelCalendar.DATE_FORMAT_SHORT_)];
      }
    }

    return 0.0;
  },

  removeOBRoomRow: function(/*HReservationObject*/ob_reserv) {
    if (!ob_reserv.room.overbooking) {
      console.warn(`[HotelCalendar][removeOBRoomRow] Can't remove the row for room ${ob_reserv.room.id}`);
      return false;
    }

    var obRoomRow = this.getOBRoomRow(ob_reserv);

    // Update Reservations Position
    var bounds = obRoomRow.getBoundingClientRect();
    var cheight = bounds.bottom-bounds.top;
    var start_index = _.indexOf(this.options.rooms, ob_reserv.room) + 1;
    for (var i=start_index; i<this.options.rooms.length; i++) {
      var reservs = this.getReservationsByRoom(this.options.rooms[i], true);
      for (var reserv of reservs) {
        var top = parseInt(reserv._html.style.top, 10);
        reserv._html.style.top = `${top - cheight}px`;
      }
    }

    obRoomRow.parentNode.removeChild(obRoomRow);
    this.options.rooms = _.reject(this.options.rooms, function(item){ return item === ob_reserv.room; });
    ob_reserv.room = false;
  },

  getOBRealRoomInfo: function(/*HRoomObject*/room) {
    // Obtain real id
    var isf = room.number.search('OB-');
    var isfb = room.number.search('/#');
    var cnumber = room.number;
    if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }

    // Obtain the original room row
    var mainRoomRowId = this._sanitizeId(`ROW_${cnumber}_${room.type}`);
    var mainRoomRow = this.e.querySelector('#'+mainRoomRowId);
    if (!mainRoomRow) {
      return false;
    }

    return [this.getRoom(mainRoomRow.dataset.hcalRoomObjId), mainRoomRow];
  },

  getOBRoomRow: function(/*HReservationObject*/ob_reserv) {
    // Obtain real id
    var isf = ob_reserv.room.number.search('OB-');
    var isfb = ob_reserv.room.number.search('/#');
    var cnumber = ob_reserv.room.number;
    if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }

    return this.e.querySelector(`#${this._sanitizeId(`ROW_${cnumber}_${ob_reserv.room.type}_OVER${ob_reserv.id}`)}`);
  },

  parseOBRoomId: function(/*String*/id) {
    if (typeof id !== 'number') {
      return id.split('@');
    }
    return id;
  },

  createOBRoom: function(/*HRoomObject*/mainRoom, /*Int*/reservId) {
    var obr = this.getOBRooms(mainRoom.id);
    // Create Overbooking Room
    var ob_room = mainRoom.clone();
    ob_room.id = `${reservId}@${mainRoom.id}`;
    ob_room.number = `OB-${mainRoom.number}/#${obr.length}`;
    ob_room.overbooking = true;
    this._insertRoomAt(mainRoom, ob_room, true);
    return ob_room;
  },

  createOBRoomRow: function(/*Int,HRoomObject*/ob_room) {
    var mainRoomInfo = this.getOBRealRoomInfo(ob_room);
    var obRoomId = this.parseOBRoomId(ob_room.id);
    if (!mainRoomInfo) {
      console.warn(`[HotelCalendar][createOBRoomRow] Can't found room row: ${mainRoomRowId}`);
      return false;
    }
    var mainRoom = mainRoomInfo[0];
    var mainRoomRow = mainRoomInfo[1];

    var row = document.createElement("TR");
    row.setAttribute('id', this._sanitizeId(`ROW_${mainRoom.number}_${ob_room.type}_OVER${obRoomId[0]}`));
    row.classList.add('hcal-row-room-type-group-item');
    row.classList.add('hcal-row-room-type-group-overbooking-item');
    row.dataset.hcalRoomObjId = ob_room.id;
    mainRoomRow.parentNode.insertBefore(row, mainRoomRow.nextSibling);

    var cell = row.insertCell();
    cell.textContent = ob_room.number;
    cell.classList.add('hcal-cell-room-type-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-3d');
    cell.setAttribute('colspan', '2');
    cell = row.insertCell();
    cell.textContent = ob_room.type;
    cell.classList.add('hcal-cell-room-type-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-flat');

    var now = moment();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`${ob_room.type}_${ob_room.number}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-room-type-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.dataset.hcalRoomObjId = ob_room.id;
      // Generate Interactive Table
      cell.appendChild(this._generateTableDay(cell, ob_room));
      //cell.innerHTML = dd.format("DD");
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    // Update Reservations Position
    var bounds = row.getBoundingClientRect();
    var cheight = bounds.bottom-bounds.top;
    var start_index = _.indexOf(this.options.rooms, ob_room) + 1;
    for (var i=start_index; i<this.options.rooms.length; i++) {
      var reservs = this.getReservationsByRoom(this.options.rooms[i], true);
      for (var reserv of reservs) {
        var top = parseInt(reserv._html.style.top, 10);
        reserv._html.style.top = `${top + cheight}px`;
      }
    }

    return row;
  },

  //==== RESTRICTIONS
  setRestrictions: function(/*Object*/restrictions) {
    this._restrictions = restrictions;
    this._updateRestrictions();
  },

  addRestrictions: function(/*Object*/restrictions) {
    var vroom_ids = Object.keys(restrictions);
    for (var vid of vroom_ids) {
      if (vid in this._restrictions) {
        this._restrictions[vid] = _.extend(this._restrictions[vid], restrictions[vid]);
      }
      else {
        this._restrictions[vid] = restrictions[vid];
      }
    }
    this._updateRestrictions();
  },

  _updateRestrictions: function() {
    // Clean
    var restDays = this.e.querySelectorAll('.hcal-restriction-room-day');
	  for (var rd of restDays) {
      rd.title = '';
      rd.classList.remove('hcal-restriction-room-day');
	  }

    if (this._restrictions) {
      // Rooms Restrictions
      for (var room of this.options.rooms) {
        if (room.price[0] == 'pricelist') {
          var date = this.options.startDate.clone().startOf('day');
          for (var i=0; i<=this.options.days; ++i) {
            var dd = date.add(1, 'd');
            var date_str = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
            if (date_str in this._restrictions[room.price[1]]) {
              var restr = this._restrictions[room.price[1]][date_str];
              if (restr) {
                var cell = this.getMainCell(dd, room.type, room.number);
                if (cell) {
                  if (restr[0] || restr[1] || restr[2] || restr[3] || restr[4] || restr[5] || restr[6]) {
                    cell.classList.add('hcal-restriction-room-day');
                    var humantext = "Restrictions:\n";
                    if (restr[0] > 0)
                      humantext += `Min. Stay: ${restr[0]}\n`;
                    if (restr[1] > 0)
                      humantext += `Min. Stay Arrival: ${restr[1]}\n`;
                    if (restr[2] > 0)
                      humantext += `Max. Stay: ${restr[2]}\n`;
                    if (restr[3] > 0)
                      humantext += `Max. Stay Arrival: ${restr[3]}\n`;
                    if (restr[4])
                      humantext += `Closed: ${restr[4]}\n`;
                    if (restr[5])
                      humantext += `Closed Arrival: ${restr[5]}\n`;
                    if (restr[6])
                      humantext += `Closed Departure: ${restr[6]}`;
                    cell.title = humantext;
                  }
                  else {
                    cell.classList.remove('hcal-restriction-room-day');
                    cell.title = '';
                  }
                }
              }
            }
          }
        }
      }
    }
  },

  //==== DETAIL CALCS
  calcDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    var day = HotelCalendar.toMoment(day);
    if (!day) {
      return false;
    }

    var reservs = this.getDayRoomTypeReservations(day, room_type);
    var num_rooms = this.getRoomsCapacityByType(room_type);
    for (var r of reservs) {
      if (r.unusedZone || r.overbooking) {
    	   continue;
      }
      num_rooms -= (r.room && r.room.shared)?r.getTotalPersons():1;
    }

    return num_rooms;
  },

  calcDayRoomTotalReservations: function(/*String,MomentObject*/day) {
    var day = HotelCalendar.toMoment(day);
    if (!day) {
      return false;
    }

    var reservs = this.getReservationsByDay(day, true);
    var num_rooms = this.getRoomsCapacityTotal();
    for (var r of reservs) {
      if (r.unusedZone || r.overbooking) {
    	   continue;
      }
      num_rooms -= (r.room && r.room.shared)?r.getTotalPersons():1;
    }

    return num_rooms;
  },

  calcReservationOccupation: function(/*String,MomentObject*/day, /*String*/room_type) {
    var day = HotelCalendar.toMoment(day);
    if (!day) {
      return false;
    }

    var reservs = this.getReservationsByDay(day, true);
    return Math.round(reservs.length/_.filter(this.options.rooms, function(item){ return !item.overbooking; }).length*100.0);
  },



  /** PRIVATE MEMBERS **/
  //==== MAIN FUNCTIONS
  _reset_action_reservation: function() {
    if (this._lazyModeReservationsSelection) {
      clearTimeout(this._lazyModeReservationsSelection);
      this._lazyModeReservationsSelection = false;
    }

    this.reservationAction = {
      action: HotelCalendar.ACTION.NONE,
      reservation: null,
      oldReservationObj: null,
      newReservationObj: null,
      mousePos: false,
      inReservations: [],
      outReservations: [],
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
    var $this = this;
  	while (this.e.hasChildNodes()) {
  		this.e.removeChild(this.e.lastChild);
  	}

    if (this._tableCreated) {
      console.warn("[Hotel Calendar][_create] Already created!");
      return false;
    }

    var scrollThrottle = _.throttle(this._updateOBIndicators.bind(this), 100);

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
    this.edivr.addEventListener("scroll", scrollThrottle, false);
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

    var observer = new MutationObserver(function(mutationsList){
      $this._updateOBIndicators();
    });
    observer.observe(this.edivr, { childList: true });

    this._updateView();
    this._tableCreated = true;

    return true;
  },

  _generateTableDay: function(/*HTMLObject*/parentCell, /*HRoomObject*/room) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var num = ((room.shared || this.options.divideRoomsByCapacity)?room.capacity:1);
    for (var i=0; i<num; i++) {
      row = table.insertRow();
      cell = row.insertCell();
      cell.dataset.hcalParentRow = parentCell.dataset.hcalParentRow;
      cell.dataset.hcalParentCell = parentCell.getAttribute('id');
      cell.dataset.hcalBedNum = i;
      cell.addEventListener('mouseenter', this._onCellMouseEnter.bind(this), false);
      cell.addEventListener('mousedown', this._onCellMouseDown.bind(this), false);
      cell.addEventListener('mouseup', this._onCellMouseUp.bind(this), false);
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
    cell.classList.add('hcal-cell-pagination');

    var button = document.createElement('button');
    button.setAttribute('id', 'cal-pag-prev-plus');
    button.classList.add('btn');
    button.style.minHeight = 0;
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.clone().subtract(this.options.paginatorStepsMax-1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone(), 'date_end': this._endDate.clone() });
    }.bind(this));
    var buttonIcon = document.createElement('i');
    buttonIcon.classList.add('fa', 'fa-2x', 'fa-angle-double-left');
    button.appendChild(buttonIcon);
    cell.appendChild(button);
    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-prev');
    button.firstElementChild.classList.remove('fa-angle-double-left');
    button.firstElementChild.classList.add('fa-angle-left');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.subtract(this.options.paginatorStepsMin-1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone(), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);

    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-selector');
    button.firstElementChild.classList.remove('fa-angle-left');
    button.firstElementChild.classList.add('fa-calendar');
    if (this.options.startDate.isSame(moment().utc().subtract(1, 'd'), 'd')) {
      // TODO
    } else {
      button.addEventListener('click', function(){
        this.setStartDate(moment().utc(), undefined, true);
        this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone(), 'date_end': this._endDate.clone() });
      }.bind(this));
    }
    cell.appendChild(button);

    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-next');
    button.firstElementChild.classList.remove('fa-calendar');
    button.firstElementChild.classList.add('fa-angle-right');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.add(this.options.paginatorStepsMin+1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone(), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);
    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-next-plus');
    button.firstElementChild.classList.remove('fa-angle-right');
    button.firstElementChild.classList.add('fa-angle-double-right');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.add(this.options.paginatorStepsMax+1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone(), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);

    var edit = document.createElement('input');
    edit.style.width = "100%";
    edit.style.display = 'block';
    edit.setAttribute('id', 'cal-search-query');
    edit.setAttribute('placeholder', 'Search...');
    cell.appendChild(edit);

    edit.addEventListener('keypress', function(ev){
      if (ev.keyCode === 13) {
        var query = ev.target.value;
        this.setDomain(HotelCalendar.DOMAIN.RESERVATIONS, [
          ['title', 'ilike', query]
        ]);
      }
    }.bind(this), false);

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
      cell.setAttribute('id', this._sanitizeId(`hday_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
        months[cur_month].year = dd_local.format('YYYY');
        months[cur_month].colspan = 0;
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
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
    for (var itemRoom of this.options.rooms) {
      // Room Number
      row = tbody.insertRow();
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      if (itemRoom.overbooking) {
        var reservId = this.parseOBRoomId(itemRoom.id)[0];
        var cnumber = itemRoom.number;
        var isf = cnumber.search('OB-');
        var isfb = cnumber.search('/#');
        if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }
        row.setAttribute('id', this._sanitizeId(`ROW_${cnumber}_${itemRoom.type}_OVER${reservId}`));
        row.classList.add('hcal-row-room-type-group-overbooking-item');
      } else {
        row.setAttribute('id', $this._sanitizeId(`ROW_${itemRoom.number}_${itemRoom.type}`));
      }
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
        cell.setAttribute('id', $this._sanitizeId(`${itemRoom.type}_${itemRoom.number}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
        cell.dataset.hcalRoomObjId = itemRoom.id;
        // Generate Interactive Table
        cell.appendChild($this._generateTableDay(cell, itemRoom));
        //cell.innerHTML = dd.format("DD");
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }

      itemRoom._html = row;
    }

    this._filterRooms();
    this._calcViewHeight();
  },

  _calcViewHeight: function() {
    if (this.options.showNumRooms > 0) {
      var rows = this.edivr.querySelectorAll('tr.hcal-row-room-type-group-item');
      var cheight = 0.0;
      for (var i=0; i<this.options.showNumRooms && i<rows.length; ++i)
      {
        var bounds = rows[i].getBoundingClientRect();
        cheight += bounds.bottom-bounds.top;
      }
      this.edivr.style.height = `${cheight}px`;
      this.edivr.style.maxHeight = 'initial';
    }
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
      cell.setAttribute('id', this._sanitizeId(`hday_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
      } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    /** DETAIL LINES **/
    var tbody = document.createElement("tbody");
    this.edtable.appendChild(tbody);
    if (this.options.showAvailability) {
      // Rooms Free Types
      if (this.options.rooms) {
        var room_types = this.getRoomTypes();
        for (var rt of room_types) {
          if (rt) {
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
              cell.setAttribute('id', this._sanitizeId(`CELL_FREE_${rt}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
              } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
                cell.classList.add('hcal-cell-end-week');
              }
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
        cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_TOTAL_FREE_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
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
        cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_PERC_OCCUP_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
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
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
    }
    // Rooms Pricelist
    this._pricelist_id = _.keys(this._pricelist)[0];
    if (this.options.showPricelist && this._pricelist) {
      //var pricelists_keys = _.keys(this._pricelist)
      //for (var key of pricelists_keys) {
      var key = this._pricelist_id;
      var pricelist = this._pricelist[key];
      for (var listitem of pricelist) {
        row = tbody.insertRow();
        row.setAttribute('id', this._sanitizeId(`ROW_DETAIL_PRICE_ROOM_${key}_${listitem.room}`));
        row.dataset.hcalPricelist = key;
        row.dataset.hcalVRoomId = listitem.room
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
          cell.setAttribute('id', this._sanitizeId(`CELL_PRICE_${key}_${listitem.room}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          cell.classList.add('hcal-cell-detail-room-price-group-item-day');
          cell.dataset.hcalParentRow = row.getAttribute('id');
          cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
          var day = +dd_local.format("D");
          if (day == 1) {
            cell.classList.add('hcal-cell-start-month');
          }
          if (dd_local.isSame(now, 'day')) {
            cell.classList.add('hcal-cell-current-day');
          } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
            cell.classList.add('hcal-cell-end-week');
          }

          var input = document.createElement('input');
          input.setAttribute('id', this._sanitizeId(`INPUT_PRICE_${key}_${listitem.room}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          input.setAttribute('type', 'edit');
          input.setAttribute('title', 'Price');
          input.dataset.hcalParentCell = cell.getAttribute('id');
          var dd_fmrt = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
          input.dataset.orgValue = input.value = _.has(listitem['days'], dd_fmrt)?Number(listitem['days'][dd_fmrt]).toLocaleString():'...';
          input.addEventListener('change', function(ev){
            var parentCell = $this.edtable.querySelector(`#${this.dataset.hcalParentCell}`);
            var parentRow = $this.edtable.querySelector(`#${parentCell.dataset.hcalParentRow}`);
            var vals = {
              'vroom_id': +parentRow.dataset.hcalVRoomId,
              'date': HotelCalendar.toMoment(parentCell.dataset.hcalDate),
              'price': this.value,
              'old_price': this.dataset.orgValue,
              'pricelist_id': +parentRow.dataset.hcalPricelist
            };
            $this.updateVRoomPrice(vals['pricelist_id'], vals['vroom_id'], vals['date'], vals['price']);
            $this._dispatchEvent('hcalOnPricelistChanged', vals);
          });
          cell.appendChild(input);
        }
      }
      //}
    }
  },

  //==== UPDATE FUNCTIONS
  _updateView: function(/*Bool*/notData, /*function*/callback) {
    this._createTableReservationDays();
    if (typeof callback !== 'undefined') {
      callback();
    }
    this._updateCellSelection();
    this._createTableDetailDays();

    _.defer(function(){
      this._updateReservations(true);
    }.bind(this));
    if (!notData) {
      _.defer(function(){
        this._updateRestrictions();
        this._updatePriceList();
        this._updateReservationOccupation();
      }.bind(this));
    }
  },

  _updateOBIndicators: function() {
    var mainBounds = this.edivr.getBoundingClientRect();
    for (var reserv of this._reservations) {
      if (reserv.overbooking && reserv._html) {
        var eOffset = this.e.getBoundingClientRect();
        var bounds = reserv._html.getBoundingClientRect();
        if (bounds.top > mainBounds.bottom) {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (!warnDiv) {
            var warnDiv = document.createElement("DIV");
            warnDiv.innerHTML = "<i class='fa fa-warning'></i>";
            warnDiv.classList.add('hcal-warn-ob-indicator');
            warnDiv.style.borderTopLeftRadius = warnDiv.style.borderTopRightRadius = "50px";
            warnDiv.dataset.hcalReservationObjId = reserv.id;
            this.e.appendChild(warnDiv);
            var warnComputedStyle = window.getComputedStyle(warnDiv, null);
            warnDiv.style.top = `${mainBounds.bottom - eOffset.top - parseInt(warnComputedStyle.getPropertyValue("height"), 10)}px`;
            warnDiv.style.left = `${(bounds.left + (bounds.right - bounds.left)/2.0 - parseInt(warnComputedStyle.getPropertyValue("width"), 10)/2.0) - mainBounds.left}px`;
          }
        } else if (bounds.bottom < mainBounds.top) {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (!warnDiv) {
            var warnDiv = document.createElement("DIV");
            warnDiv.innerHTML = "<i class='fa fa-warning'></i>";
            warnDiv.classList.add('hcal-warn-ob-indicator');
            warnDiv.style.borderBottomLeftRadius = warnDiv.style.borderBottomRightRadius = "50px";
            warnDiv.style.top = `${mainBounds.top - eOffset.top}px`;
            warnDiv.dataset.hcalReservationObjId = reserv.id;
            this.e.appendChild(warnDiv);
            var warnComputedStyle = window.getComputedStyle(warnDiv, null);
            warnDiv.style.left = `${(bounds.left + (bounds.right - bounds.left)/2.0 - parseInt(warnComputedStyle.getPropertyValue("width"), 10)/2.0) - mainBounds.left}px`;
          }
        } else {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (warnDiv) {
            warnDiv.parentNode.removeChild(warnDiv);
          }
        }
      }
    }
  },

  _updateHighlightSwapReservations: function() {
    var $this = this;
    if (this.reservationAction.inReservations.length === 0 && this.reservationAction.outReservations.length === 0) {
      var elms = this.e.querySelectorAll("div.hcal-reservation-invalid-swap");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-invalid-swap'); }
      elms = this.e.querySelectorAll("div.hcal-reservation-swap-in-selected");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-swap-in-selected'); }
      elms = this.e.querySelectorAll("div.hcal-reservation-swap-out-selected");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-swap-out-selected'); }
    }
    else {
      var dateLimits = this.getDateLimits(this.reservationAction.inReservations);
      var inMaxPersons = _.max(this.reservationAction.inReservations, function(item) { return item.getTotalPersons(); }).getTotalPersons();
      var outMaxPersons = this.reservationAction.outReservations.length>0?_.max(this.reservationAction.outReservations, function(item) { return item.getTotalPersons(); }).getTotalPersons():false;
      var refInReservation = this.reservationAction.inReservations[0];
      var refOutReservation = this.reservationAction.outReservations[0];
      var realDateLimits = this.getFreeDatesByRoom(dateLimits[0], dateLimits[1], refInReservation?refInReservation.room.id:refOutReservation.room.id);
      for (var nreserv of this._reservations) {
        if (nreserv._html.classList.contains('hcal-reservation-swap-in-selected') || nreserv._html.classList.contains('hcal-reservation-swap-out-selected')) {
          continue;
        }

        // Invalid capacity
        if (nreserv.getTotalPersons() > inMaxPersons || (outMaxPersons && nreserv.getTotalPersons() > outMaxPersons))
        {
          nreserv._html.classList.add('hcal-reservation-invalid-swap');
        }
        else if (this._modeSwap === HotelCalendar.MODE.SWAP_FROM && this.reservationAction.inReservations.length !== 0 && refInReservation.room.id !== nreserv.room.id) {
          if (!_.find(this.reservationAction.outReservations, {'id': nreserv.linkedId})) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        } else if (this._modeSwap === HotelCalendar.MODE.SWAP_TO && this.reservationAction.outReservations.length !== 0 && refOutReservation.room.id !== nreserv.room.id) {
          if (!_.find(this.reservationAction.inReservations, {'id': nreserv.linkedId})) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        }
        // Invalid reservations out of dates
        else if (nreserv.startDate.isBefore(realDateLimits[0], 'day') || nreserv.endDate.isAfter(realDateLimits[1], 'day')) {
          if (nreserv.room.id !== refInReservation.room.id) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        }
        else {
          // var reservs = this.getReservationsByRoom(nreserv.room, false);
          // var hasInvalidReservs = false;
          // for (var r of reservs) {
          //   if (r._html.classList.contains('hcal-reservation-invalid-swap') && nreserv.startDate.isSameOrAfter(realDateLimits[0], 'day') && nreserv.endDate.isSameOrBefore(realDateLimits[1], 'day')) {
          //     hasInvalidReservs = true;
          //     break;
          //   }
          // }
          // var nrealDateLimits = this.getFreeDatesByRoom(nreserv.startDate, nreserv.endDate, nreserv.room.number);
          // if (hasInvalidReservs && (nrealDateLimits[0].isAfter(realDateLimits[0], 'day') || nrealDateLimits[1].isBefore(realDateLimits[1], 'day'))) {
          //   if (nreserv.room.id !== refInReservation.room.id) {
          //     nreserv._html.classList.add('hcal-reservation-invalid-swap');
          //   }
          // }
          // // Is a valid reservation
          // else
          // {
            nreserv._html.classList.remove('hcal-reservation-invalid-swap');
          // }
        }
      }
    }
  },

  _updateHighlightInvalidZones: function(/*HReservation*/reserv) {
    if (typeof reserv === 'undefined') {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.remove('hcal-cell-invalid');
      }
      return;
    }

    if (reserv.readOnly) {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.add('hcal-cell-invalid');
      }
    } else if (reserv.fixDays) {
      var limitLeftDate = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitRightDate = this.etable.querySelector(`#${reserv._limits.right.dataset.hcalParentCell}`).dataset.hcalDate;
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
      var parentCell = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`);
      var parent_row = parentCell.dataset.hcalParentRow;
      var elms = this.etable.querySelectorAll("td:not([data-hcal-parent-row='"+parent_row+"']) table td");
      for (var tdCell of elms) {
        tdCell.classList.add('hcal-cell-invalid');
      }
    } else {
      var limitLeftDate = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitRightDate = this.etable.querySelector(`#${reserv._limits.right.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitLeftDateMoment = HotelCalendar.toMoment(limitLeftDate);
      var limitRightDateMoment = HotelCalendar.toMoment(limitRightDate);
      var diff_date = this.getDateDiffDays(limitLeftDateMoment, limitRightDateMoment);
      var date = limitLeftDateMoment.clone().startOf('day');
      var selector = [];
      for (var i=0; i<=diff_date; i++) {
        selector.push("td[data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'] table td");
        date.add(1, 'd');
      }
      if (selector.length) {
        var elms = this.etable.querySelectorAll(`${selector.join(', ')}`);
        for (var tdCell of elms) {
          tdCell.classList.add('hcal-cell-highlight');
        }
      }
    }
  },

  _updateScroll: function(/*HTMLObject*/reservationDiv) {
    var reservBounds = reservationDiv.getBoundingClientRect();
    var mainBounds = this.edivr.getBoundingClientRect();
    var eOffset = this.e.getBoundingClientRect();
    var bottom = mainBounds.bottom - eOffset.top;
    var top = mainBounds.top + eOffset.top;
    var offset = 10.0;
    var scrollDisp = 10.0;
    if (reservBounds.bottom >= bottom-offset) {
      this.edivr.scrollBy(0, scrollDisp);
    }
    else if (reservBounds.top <= top+offset) {
      this.edivr.scrollBy(0, -scrollDisp);
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
      if (this._cellSelection.current) {
        this._cellSelection.current.classList.add('hcal-cell-highlight');
      }
      // Highlight Range Cells
      var cells = false;
      var total_price = 0.0;
      var limits = new HLimit(this._cellSelection.start,
                              this._cellSelection.end?this._cellSelection.end:this._cellSelection.current);
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
          var parentRow = this.$base.querySelector(`#${c.dataset.hcalParentRow}`);
          var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
          if (room.overbooking) {
            continue;
          }
          c.classList.add('hcal-cell-highlight');
          if (this._pricelist) {
            // FIXME: Normalize data calendar (gmt) vs extra info (utc)
            var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${c.dataset.hcalParentCell}`).dataset.hcalDate);
            var room_price = this.getRoomPrice(parentRow.dataset.hcalRoomObjId, date_cell);
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

      this._dispatchEvent(
        'hcalOnUpdateSelection',
          {
            'limits': limits,
            'cells': cells,
            'old_cells': highlighted_td,
            'totalPrice': total_price
          });
  },

  _resetCellSelection: function() {
    this._cellSelection = { current: false, end: false, start: false };
  },

  //==== RESERVATIONS
  _updateDivReservation: function(/*HReservationObject*/reserv, /*Bool?*/noRefresh) {
    if (!reserv._limits.isValid() || !reserv._html) {
      return;
    }

    if (reserv.readOnly) {
      reserv._html.classList.add('hcal-reservation-readonly');
    } else {
      reserv._html.classList.remove('hcal-reservation-readonly');
    }

    if (reserv.room._active) {
      reserv._html.classList.remove('hcal-hidden');
    } else {
      reserv._html.classList.add('hcal-hidden');
    }

    if (reserv._active) {
      reserv._html.classList.remove('hcal-reservation-unselect');
    } else {
      reserv._html.classList.add('hcal-reservation-unselect');
    }

    if (!noRefresh) {
      var numBeds = (+reserv._limits.right.dataset.hcalBedNum)-(+reserv._limits.left.dataset.hcalBedNum);
      reserv._beds = [];
      for (var i=0; i<=numBeds; reserv._beds.push(+reserv._limits.left.dataset.hcalBedNum+i++));

      var boundsInit = reserv._limits.left.getBoundingClientRect();
      var boundsEnd = reserv._limits.right.getBoundingClientRect();

      reserv._html.removeAttribute('style');

      if (reserv.splitted) {
        reserv._html.classList.add('hcal-reservation-splitted');
        var magicNumber = Math.floor(Math.abs(Math.sin((reserv.getUserData('parent_reservation') || reserv.id))) * 100000);
        var bbColor = this._intToRgb(magicNumber);
        reserv._html.style.borderColor = `rgb(${bbColor[0]},${bbColor[1]},${bbColor[2]})`;
      } else {
        reserv._html.classList.remove('hcal-reservation-splitted');
      }
      reserv._html.style.backgroundColor = reserv.color;
      reserv._html.style.color = reserv.colorText;

      var etableOffset = this.etable.getBoundingClientRect();

      reserv._html.style.top = `${boundsInit.top-etableOffset.top}px`;
      var divHeight = (boundsEnd.bottom-etableOffset.top)-(boundsInit.top-etableOffset.top);
      reserv._html.style.height = `${divHeight}px`;
      reserv._html.style.lineHeight = `${divHeight}px`;
      var fontHeight = divHeight/1.3;
      if (fontHeight > 16) {
        fontHeight = 16;
      }
      reserv._html.style.fontSize = `${fontHeight}px`;

      var clearBorderLeft = function(/*HTMLObject*/elm) {
        elm.style.borderLeftWidth = '0';
        elm.style.borderTopLeftRadius = '0';
        elm.style.borderBottomLeftRadius = '0';
      };
      var clearBorderRight = function(/*HTMLObject*/elm) {
        elm.style.borderRightWidth = '0';
        elm.style.borderTopRightRadius = '0';
        elm.style.borderBottomRightRadius = '0';
      };

      if (reserv._drawModes[0] === 'soft-start' && reserv._drawModes[1] === 'soft-end') {
        clearBorderLeft(reserv._html);
        clearBorderRight(reserv._html);
        reserv._html.style.left = `${boundsInit.left-etableOffset.left}px`;
        reserv._html.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width}px`;
      } else if (reserv._drawModes[0] === 'soft-start') {
        clearBorderLeft(reserv._html);
        reserv._html.style.left = `${boundsInit.left-etableOffset.left}px`;
        reserv._html.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0}px`;
      } else if (reserv._drawModes[1] === 'soft-end') {
        clearBorderRight(reserv._html);
        reserv._html.style.left = `${boundsInit.left-etableOffset.left+boundsInit.width/2.0}px`;
        reserv._html.style.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width}px`;
      } else {
        reserv._html.style.left = `${(boundsInit.left-etableOffset.left)+boundsEnd.width/2.0}px`;
        reserv._html.style.width = `${(boundsEnd.left-boundsInit.left)}px`;
      }
    }
  },

  swapReservations: function(/*List HReservationObject*/fromReservations, /*List HReservationObject*/toReservations) {
    if (fromReservations.length === 0 || toReservations.length === 0) {
      console.warn("[HotelCalendar][swapReservations] Invalid Swap Operation!");
      return false;
    }
    var fromDateLimits = this.getDateLimits(fromReservations);
    var fromRealDateLimits = this.getFreeDatesByRoom(fromDateLimits[0], fromDateLimits[1], fromReservations[0].room.id);
    var toDateLimits = this.getDateLimits(toReservations);
    var toRealDateLimits = this.getFreeDatesByRoom(toDateLimits[0], toDateLimits[1], toReservations[0].room.id);

    if (fromDateLimits[0].isSameOrAfter(toRealDateLimits[0], 'd') && fromDateLimits[1].isSameOrBefore(toRealDateLimits[1], 'd') &&
        toDateLimits[0].isSameOrAfter(fromRealDateLimits[0], 'd') && toDateLimits[1].isSameOrBefore(fromRealDateLimits[1], 'd'))
    {
      // Change some critical values
      var refFromReservs = fromReservations[0];
      var refToReservs = toReservations[0];
      var refFromRoom = refFromReservs.room;
      var refToRoom = refToReservs.room;
      var fromRoomRow = this.getOBRoomRow(refFromReservs);
      var toRoomRow = this.getOBRoomRow(refToReservs);
      var refFromRoomNewId = refFromRoom.overbooking?this.parseOBRoomId(refFromRoom.id)[1]:refFromRoom.id;
      refFromRoomNewId = `${refToReservs.id}@${refFromRoomNewId}`;
      var refToRoomNewId = refToRoom.overbooking?this.parseOBRoomId(refToRoom.id)[1]:refToRoom.id;
      refToRoomNewId = `${refFromReservs.id}@${refToRoomNewId}`;

      if (refFromRoom.overbooking) {
        // Obtain real id
        var isf = refFromReservs.room.number.search('OB-');
        var isfb = refFromReservs.room.number.search('/#');
        var cnumber = refFromReservs.room.number;
        if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }

        refFromRoom.id = refFromRoomNewId;
        var newRowId = `${this._sanitizeId(`ROW_${cnumber}_${refToRoom.type}_OVER${refToReservs.id}`)}`;
        var elms = fromRoomRow.querySelectorAll(`td[data-hcal-parent-row='${fromRoomRow.id}']`);
        for (var elm of elms) { elm.dataset.hcalParentRow = newRowId; }
        fromRoomRow.setAttribute('id', `${newRowId}`);
        fromRoomRow.dataset.hcalRoomObjId = refFromRoom.id;
      }
      if (refToRoom.overbooking) {
        // Obtain real id
        var isf = refToReservs.room.number.search('OB-');
        var isfb = refToReservs.room.number.search('/#');
        var cnumber = refToReservs.room.number;
        if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }

        refToRoom.id = refToRoomNewId;
        var newRowId = `${this._sanitizeId(`ROW_${cnumber}_${refFromRoom.type}_OVER${refFromReservs.id}`)}`;
        var elms = toRoomRow.querySelectorAll(`td[data-hcal-parent-row='${toRoomRow.id}']`);
        for (var elm of elms) { elm.dataset.hcalParentRow = newRowId; }
        toRoomRow.setAttribute('id', `${newRowId}`);
        toRoomRow.dataset.hcalRoomObjId = refToRoom.id;
      }

      for (var nreserv of fromReservations) {
        nreserv.overbooking = refToRoom.overbooking;
        nreserv.room = refToRoom;
      }
      for (var nreserv of toReservations) {
        nreserv.overbooking = refToRoom.overbooking;
        nreserv.room = refFromRoom;
      }

      if (this.options.divideRoomsByCapacity) {
        var allReservs = toReservations.concat(fromReservations);
        for (var nreserv of allReservs) { this._updateUnusedZones(nreserv); }
      }
    } else {
      console.warn("[HotelCalendar][swapReservations] Invalid Swap Operation!");
      return false;
    }

    return true;
  },

  _dispatchSwapReservations: function() {
    if (this.reservationAction.inReservations.length > 0 && this.reservationAction.outReservations.length > 0) {
      this._dispatchEvent(
        'hcalOnSwapReservations',
        {
          'inReservs': this.reservationAction.inReservations || [],
          'outReservs': this.reservationAction.outReservations || [],
        }
      );
    }
  },

  replaceReservation: function(/*HReservationObject*/reservationObj, /*HReservationObject*/newReservationObj) {
    if (!reservationObj._html) {
      console.warn("[Hotel Calendar][updateReservation_] Invalid Reservation Object");
      return;
    }

    var index = _.findKey(this._reservations, {'id': reservationObj.id});
    delete this._reservations[index];
    this._reservations[index] = newReservationObj;
    reservationObj._html.dataset.hcalReservationObjId = newReservationObj.id;
    this._updateReservationsMap();
    this._updateDivReservation(newReservationObj);

    var linkedReservations = this.getLinkedReservations(newReservationObj);
    for (var lr of linkedReservations) {
      lr.startDate = newReservationObj.startDate.clone();
      lr.endDate = newReservationObj.endDate.clone();

      if (lr._html) {
        this._calcReservationCellLimits(lr);
        this._updateDivReservation(lr);
      }
    }
    _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
  },

  getLinkedReservations: function(/*HReservationObject*/reservationObj) {
    return _.reject(this._reservations, function(item){ return item === reservationObj || item.linkedId !== reservationObj.id; });
  },

  _updateReservation: function(/*HReservationObject*/reservationObj, /*Bool?*/noRefresh) {
    // Fill
    if (reservationObj._limits.isValid()) {
      this._updateDivReservation(reservationObj, noRefresh);
    } else {
      console.warn(`[Hotel Calendar][_updateReservation] Can't place reservation ID@${reservationObj.id} [${reservationObj.startDate.format(HotelCalendar.DATE_FORMAT_LONG_)} --> ${reservationObj.endDate.format(HotelCalendar.DATE_FORMAT_LONG_)}]`);
      this.removeReservation(reservationObj);
    }
  },

  _updateReservations: function(/*Bool*/updateLimits) {
      for (var reservation of this._reservations){
        if (updateLimits) {
          this._calcReservationCellLimits(reservation);
        }
        this._updateReservation(reservation);
      }
      //this._assignReservationsEvents();
      //this._updateReservationOccupation();
      this._updateOBIndicators();
  },

  _assignReservationsEvents: function(reservDivs) {
    var $this = this;
    reservDivs = reservDivs || this.e.querySelectorAll('div.hcal-reservation');
    for (var rdiv of reservDivs) {
      var bounds = rdiv.getBoundingClientRect();
      rdiv.addEventListener('mousemove', function(ev){
        var posAction = $this._getRerservationPositionAction(this, ev.layerX, ev.layerY);
        this.style.cursor = (posAction == HotelCalendar.ACTION.MOVE_LEFT || posAction == HotelCalendar.ACTION.MOVE_RIGHT)?'col-resize':'pointer';
      }, false);
      var _funcEvent = function(ev){
        if ($this._isLeftButtonPressed(ev)) {
          if (ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_FROM) {
            $this.reservationAction.action = HotelCalendar.ACTION.SWAP;
            $this.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
          }
          // MODE SWAP RESERVATIONS
          if ($this.reservationAction.action === HotelCalendar.ACTION.SWAP) {
            var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
            var refFromReserv = ($this.reservationAction.inReservations.length > 0)?$this.reservationAction.inReservations[0]:false;
            var refToReserv = ($this.reservationAction.outReservations.length > 0)?$this.reservationAction.outReservations[0]:false;

            if (ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_FROM) {
              var canAdd = !((!refFromReserv && refToReserv && reserv.room.id === refToReserv.room.id) || (refFromReserv && reserv.room.id !== refFromReserv.room.id));
              // Can unselect
              if ($this.reservationAction.inReservations.indexOf(reserv) != -1 && (($this.reservationAction.outReservations.length > 0 && $this.reservationAction.inReservations.length > 1) || $this.reservationAction.outReservations.length === 0)) {
                $this.reservationAction.inReservations = _.reject($this.reservationAction.inReservations, function(item){ return item === reserv});
                this.classList.remove('hcal-reservation-swap-in-selected');
              }
              // Can't add a 'out' reservation in 'in' list
              else if ($this.reservationAction.outReservations.indexOf(reserv) == -1 && canAdd) {
                $this.reservationAction.inReservations.push(reserv);
                this.classList.add('hcal-reservation-swap-in-selected');
              }
            } else if (!ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_TO) {
              $this.setSwapMode(HotelCalendar.MODE.SWAP_TO);
              var canAdd = !((!refToReserv && refFromReserv && reserv.room.id === refFromReserv.room.id) || (refToReserv && reserv.room.id !== refToReserv.room.id));
              // Can unselect
              if ($this.reservationAction.outReservations.indexOf(reserv) != -1) {
                $this.reservationAction.outReservations = _.reject($this.reservationAction.outReservations, function(item){ return item === reserv; });
                this.classList.remove('hcal-reservation-swap-out-selected');
              }
              // Can't add a 'in' reservation in 'out' list
              else if ($this.reservationAction.inReservations.indexOf(reserv) == -1 && canAdd) {
                $this.reservationAction.outReservations.push(reserv);
                this.classList.add('hcal-reservation-swap-out-selected');
              }
            }
            $this._updateHighlightSwapReservations();
          }
          // MODE RESIZE/MOVE RESERVATION
          else if (!$this.reservationAction.reservation) {
            $this.reservationAction = {
              reservation: this,
              mousePos: [ev.x, ev.y],
              action: $this._getRerservationPositionAction(this, ev.layerX, ev.layerY),
              inReservations: [],
              outReservations: [],
            };

            // FIXME: Workaround for lazy selection operation
            if ($this._lazyModeReservationsSelection) {
              clearTimeout($this._lazyModeReservationsSelection);
              $this._lazyModeReservationsSelection = false;
            }

            $this._lazyModeReservationsSelection = setTimeout(function($this){
              var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
              $this._updateHighlightInvalidZones(reserv);
              if (reserv.readOnly || (reserv.fixDays && ($this.reservationAction.action == HotelCalendar.ACTION.MOVE_LEFT ||
                    $this.reservationAction.action == HotelCalendar.ACTION.MOVE_RIGHT))) {
                $this.reservationAction.action = HotelCalendar.ACTION.NONE;
                return false;
              }
              var affectedReservations = [reserv].concat($this.getLinkedReservations(reserv));
              for (var areserv of affectedReservations) {
                if (areserv._html) {
                  areserv._html.classList.add('hcal-reservation-action');
                }
              }

              var otherReservs = _.difference($this._reservations, affectedReservations);
              for (var oreserv of otherReservs) {
                if (oreserv._html) {
                  oreserv._html.classList.add('hcal-reservation-foreground');
                }
              }

              $this._lazyModeReservationsSelection = false;
            }.bind(this, $this), 100);
          }
        }
      };
      rdiv.addEventListener('mousedown', _funcEvent, false);
      rdiv.addEventListener('touchstart', _funcEvent, false);
      rdiv.addEventListener('mouseenter', function(ev){
        $this._dispatchEvent(
          'hcalOnMouseEnterReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
      rdiv.addEventListener('mouseleave', function(ev){
        $this._dispatchEvent(
          'hcalOnMouseLeaveReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
    }
  },

  _getRerservationPositionAction: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
    var bounds = elm.getBoundingClientRect();
    if (posX <= 5) { return HotelCalendar.ACTION.MOVE_LEFT; }
    else if (posX >= bounds.width-10) { return HotelCalendar.ACTION.MOVE_RIGHT; }
    return HotelCalendar.ACTION.MOVE_ALL;
  },

  // _getRerservationPositionAction: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
  //   var bounds = elm.getBoundingClientRect();
  //   var mouseActMargin = 10*bounds.width*0.01;
  //   console.log("------- Esta aiki");
  //   console.log(posX);
  //   var ppOsX = posX - posX*(1.0-window.devicePixelRatio);
  //   posX -= ppOsX;
  //   console.log(posX);
  //   var mouseActMarginV = (10*bounds.width)/100;
  //   //debugger;
  //   if (posX <= mouseActMargin) { return HotelCalendar.ACTION.MOVE_LEFT; }
  //   else if (posX >= bounds.width-mouseActMargin) { return HotelCalendar.ACTION.MOVE_RIGHT; }
  //   return HotelCalendar.ACTION.MOVE_ALL;
  // },

  _cleanUnusedZones: function(/*HReservationObject*/reserv) {
    var reservs = _.filter(this._reservations, function(item){ return item.unusedZone && item.linkedId === reserv.id; });
    for (var creserv of reservs) { this.removeReservation(creserv); }
  },

  _createUnusedZones: function(/*Array*/reservs) {
    var nreservs = [];
    for (var reserv of reservs) {
      if (!reserv.unusedZone) {
        var unused_id = 0;
        var numBeds = reserv.getTotalPersons();
      	for (var e=numBeds; e<reserv.room.capacity; ++e) {
      		nreservs.push(new HReservation({
            'id': `${reserv.id}@${--unused_id}`,
            'room': reserv.room,
            'title': '',
            'adults': 1,
            'childrens': 0,
            'startDate': reserv.startDate.clone(),
            'endDate': reserv.endDate.clone(),
            'color': '#c2c2c2',
            'colorText': '#c2c2c2',
            'splitted': false,
            'readOnly': true,
            'fixDays': true,
            'fixRooms': true,
            'unusedZone': true,
            'linkedId': reserv.id,
            'state': 'draft',
          }));
      	}
      }
    }
    return nreservs;
  },

  _updateUnusedZones: function(/*HReservationObject*/reserv) {
    if (!reserv.unusedZone) {
      // TODO: Improve this... don't remove stuff that recreate before!!!
      this._cleanUnusedZones(reserv);
    	this.addReservations(this._createUnusedZones([reserv]), true);
    }
  },

  _updateReservationOccupation: function() {
    if (!this.options.showAvailability) {
      return;
    }
    var cells = [
      this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-type-group-item-day'),
      this.edtable.querySelectorAll('td.hcal-cell-detail-room-free-total-group-item-day'),
      this.edtable.querySelectorAll('td.hcal-cell-detail-room-perc-occup-group-item-day')
    ];
    for (var i=0; i<=this.options.days; ++i) {
      var cell = false;
      // Occupation by Type
      cell = cells[0][i];
      if (cell) {
        var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
        var cell_date = cell.dataset.hcalDate;
        var num_rooms = this.getRoomsCapacityByType(parentRow.dataset.hcalRoomType);
        var num_free = this.calcDayRoomTypeReservations(cell_date, parentRow.dataset.hcalRoomType);
        cell.innerText = num_free;
        cell.style.backgroundColor = this._generateColor(num_free, num_rooms, 0.35, true, true);
      }

      // Occupation Total
      cell = cells[1][i];
      if (cell) {
        var cell_date = cell.dataset.hcalDate;
        var num_rooms = this.getRoomsCapacityTotal();
        var num_free = this.calcDayRoomTotalReservations(cell_date);
        cell.innerText = num_free;
        cell.style.backgroundColor = this._generateColor(num_free, num_rooms, 0.35, true, true);
      }

      // Occupation Total Percentage
      cell = cells[2][i];
      if (cell) {
        var parentRow = this.$base.querySelector(`#${cell.dataset.hcalParentRow}`);
        var cell_date = cell.dataset.hcalDate;
        var num_rooms = this.getRoomsCapacityTotal();
        var num_free = this.calcDayRoomTotalReservations(cell_date);
        var perc = 100.0 - (num_free * 100.0 / num_rooms);
        cell.innerText = perc.toFixed(0);
        cell.style.backgroundColor = this._generateColor(perc, 100.0, 0.35, false, true);
      }
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
          if (!(k in this._pricelist)) {
            this._pricelist[k] = [];
          }
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

  updateVRoomPrice: function(pricelist_id, vroom_id, date, price) {
    var strDate = date.format(HotelCalendar.DATE_FORMAT_SHORT_);
    var cellId = this._sanitizeId(`CELL_PRICE_${pricelist_id}_${vroom_id}_${strDate}`);
    var input = this.edtable.querySelector(`#${cellId} input`);
    if (input) {
      input.dataset.orgValue = input.value = price;
      var pr_fk = _.findKey(this._pricelist[pricelist_id], {'room': vroom_id});
      this._pricelist[pricelist_id][pr_fk].days[strDate] = price;
    }
  },

  _updatePriceList: function() {
    if (!this.options.showPricelist) {
      return;
    }
    var keys = _.keys(this._pricelist);
    for (var k of keys) {
      var pr = this._pricelist[k];
      for (var pr_item of pr) {
        var pr_keys = _.keys(pr_item['days']);
        for (var prk of pr_keys) {
          var price = pr_item['days'][prk];
          var inputId = this._sanitizeId(`INPUT_PRICE_${k}_${pr_item['room']}_${prk}`);
          var input = this.edtable.querySelector(`#${inputId}`);
          if (input) {
            input.value = Number(price).toLocaleString();
          }
        }
      }
    }
  },

  //==== HELPER FUNCTIONS
  _in_domain: function(/*HRoomObject/HReservationObject*/obj, /*Array*/domain) {
    if (!domain || domain.length === 0) {
      return true;
    }

    var founded = false;
    for (var f of domain) {
      if (typeof f[2] === 'object' && f[2].length === 0) {
        continue;
      }

      var fieldName = f[0].toLowerCase();
      var compMode = f[1].toLowerCase();
      if (compMode === 'ilike') {
        var value = f[2].toLowerCase();
        var userData = obj.getUserData(fieldName) && obj.getUserData(fieldName).toLowerCase() || '';
        if ((fieldName in obj && obj[fieldName].toLowerCase().search(value) !== -1) || userData.search(value) !== -1) {
          founded = true;
          break;
        }
      } else if (compMode === '=') {
        if ((fieldName in obj && obj[fieldName] === f[2]) ||
            obj.getUserData(fieldName) === f[2]) {
          founded = true;
          break;
        }
      } else if (compMode === 'in') {
        if ((fieldName in obj && obj[fieldName] in f[2]) ||
            obj.getUserData(fieldName) in f[2] ||
            (obj[fieldName] && typeof obj[fieldName] === 'object' && _.every(obj[fieldName], function(item) { return f[2].indexOf(item) !== -1; })) ||
            (obj.getUserData(fieldName) && typeof obj.getUserData(fieldName) === 'object' && _.every(obj.getUserData(fieldName), function(item) { return f[2].indexOf(item) !== -1; }))) {
          founded = true;
          break;
        }
      } else if (compMode === 'some') {
        if ((obj[fieldName] && typeof obj[fieldName] === 'object' && _.some(obj[fieldName], function(item) { return f[2].indexOf(item) !== -1; })) ||
            (obj.getUserData(fieldName) && typeof obj.getUserData(fieldName) === 'object' && _.some(obj.getUserData(fieldName), function(item) { return f[2].indexOf(item) !== -1; }))) {
          founded = true;
          break;
        }
      }
    }

    return founded;
  },

  getDateDiffDays: function(/*MomentObject*/start, /*MomentObject*/end) {
	  return end.clone().startOf('day').diff(start.clone().startOf('day'), 'days');
  },

  getDateLimits: function(/*List HReservationObject*/reservs) {
    var start_date = false;
    var end_date = false;
    for (var creserv of reservs) {
      if (!start_date) { start_date = creserv.startDate; }
      else if (creserv.startDate.isBefore(start_date, 'day')) {
        start_date = creserv.startDate;
      }
      if (!end_date) { end_date = creserv.endDate; }
      else if (creserv.endDate.isAfter(end_date, 'day')) {
        end_date = creserv.endDate;
      }
    }

    return [start_date, end_date];
  },

  getFreeDatesByRoom: function(/*MomentObject*/dateStart, /*MomentObject*/dateEnd, /*Int*/roomId) {
    var daysLeft = this.getDateDiffDays(this.options.startDate, dateStart);
    var daysRight = this.getDateDiffDays(dateEnd, this._endDate);
    var freeDates = [dateStart, dateEnd];

    for (var i=1; i<daysLeft; i++) {
      var ndate = dateStart.clone().subtract(i, 'd');
      var reservs = this.getReservationsByDay(ndate, false, false, roomId);
      if (reservs.length != 0) { break; }
      freeDates[0] = ndate;
    }
    for (var i=1; i<daysRight; i++) {
      var ndate = dateEnd.clone().add(i, 'd');
      var reservs = this.getReservationsByDay(ndate, false, false, roomId);
      if (reservs.length != 0) { break; }
      freeDates[1] = ndate;
    }

    return freeDates;
  },

  _dispatchEvent: function(/*String*/eventName, /*Dictionary*/data) {
    this.e.dispatchEvent(new CustomEvent(eventName, { 'detail': data }));
  },

  _sanitizeId: function(/*String*/str) {
    return str.replace(/[^a-zA-Z0-9\-_]/g, '_');
  },

  _isLeftButtonPressed: function(/*EventObject*/evt) {
    evt = evt || window.event;
    if (evt.touched && evt.touched.length) {
      return true;
    }
    return ("buttons" in evt)?(evt.buttons === 1):(evt.which || evt.button);
  },

  toAbbreviation: function(/*String*/word, /*Int*/max) {
    return word.replace(/[aeiouáéíóúäëïöü]/gi,'').toUpperCase().substr(0, max || 3);
  },

  checkReservationPlace: function(/*HReservationObject*/reservationObj) {
    var persons = reservationObj.getTotalPersons();
    if (((reservationObj.room.shared || this.options.divideRoomsByCapacity) && reservationObj._beds.length < persons)
      || (!(reservationObj.room.shared || this.options.divideRoomsByCapacity) && persons > reservationObj.room.capacity)) {
      return false;
    }

    if (reservationObj.room.id in this._reservationsMap) {
      for (var r of this._reservationsMap[reservationObj.room.id]) {
        if (!r.unusedZone && r !== reservationObj && reservationObj.room.number == r.room.number &&
            (_.difference(reservationObj._beds, r._beds).length != reservationObj._beds.length || this.options.divideRoomsByCapacity) &&
            (r.startDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day', '[)') ||
              r.endDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day', '(]') ||
              (reservationObj.startDate.isSameOrAfter(r.startDate, 'day') && reservationObj.endDate.isSameOrBefore(r.endDate, 'day')))) {
          return false;
        }
      }
    }

    return true;
  },

  //==== EVENT FUNCTIONS
  _onCellMouseUp: function(ev) {
    if (this._cellSelection.start &&
        this._cellSelection.start != ev.target &&
        this._cellSelection.start.dataset.hcalParentRow === ev.target.dataset.hcalParentRow) {
      this._cellSelection.end = ev.target;

      this._dispatchEvent(
        'hcalOnChangeSelection',
        {
          'cellStart': this._cellSelection.start,
          'cellEnd': this._cellSelection.end
        });
    }
  },

  _onCellMouseDown: function(ev) {
    this._cellSelection.start = this._cellSelection.current = ev.target;
    this._cellSelection.end = false;
    this._updateCellSelection();
  },

  _onCellMouseEnter: function(ev) {
    var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${ev.target.dataset.hcalParentCell}`).dataset.hcalDate);
    if (this._isLeftButtonPressed(ev)) {
      var reserv = null;
      var toRoom = undefined;
      var needUpdate = false;
      if (!this.reservationAction.reservation) {
        if (this._cellSelection.start && this._cellSelection.start.dataset.hcalParentRow === ev.target.dataset.hcalParentRow) {
          this._cellSelection.current = ev.target;
        }
        this._updateCellSelection();
      } else if (this.reservationAction.mousePos) {
        // workarround for not trigger reservation change
        var a = this.reservationAction.mousePos[0] - ev.x;
        var b = this.reservationAction.mousePos[1] - ev.y;
        //var dist = Math.sqrt(a*a + b*b);
        if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_RIGHT) {
          reserv = this.getReservation(this.reservationAction.reservation.dataset.hcalReservationObjId);
          if (reserv.fixDays) {
            this._reset_action_reservation();
            return true;
          }
          if (!date_cell.isAfter(reserv.startDate, 'd')) {
            date_cell = reserv.startDate.clone().startOf('day').add(1, 'd');
          }
          if (!this.reservationAction.oldReservationObj) {
            this.reservationAction.oldReservationObj = reserv.clone();
          }
          reserv.endDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
          this.reservationAction.newReservationObj = reserv;
          needUpdate = true;
        } else if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_LEFT) {
          reserv = this.getReservation(this.reservationAction.reservation.dataset.hcalReservationObjId);
          if (reserv.fixDays) {
            this._reset_action_reservation();
            return true;
          }
          var ndate = reserv.endDate.clone().endOf('day').subtract(1, 'd');
          if (!date_cell.isBefore(ndate, 'd')) {
            date_cell = ndate;
          }
          if (!this.reservationAction.oldReservationObj) {
            this.reservationAction.oldReservationObj = reserv.clone();
          }
          reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
          this.reservationAction.newReservationObj = reserv;
          needUpdate = true;
        } else if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_ALL) {
          reserv = this.getReservation(this.reservationAction.reservation.dataset.hcalReservationObjId);
          if (!this.reservationAction.oldReservationObj) {
            this.reservationAction.oldReservationObj = reserv.clone();
            this.reservationAction.daysOffset = this.getDateDiffDays(reserv.startDate.clone().local(), date_cell);
            if (this.reservationAction.daysOffset < 0 ) {
              this.reservationAction.daysOffset = 0;
            }
          }

          // Relative Movement
          date_cell.subtract(this.reservationAction.daysOffset, 'd');

          var parentRow = ev.target.parentNode.parentNode.parentNode.parentNode;
          var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
          reserv.room = room;
          var diff_date = this.getDateDiffDays(reserv.startDate, reserv.endDate);
          reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
          var date_end = reserv.startDate.clone().add(diff_date, 'd');
          reserv.endDate.set({'date': date_end.date(), 'month': date_end.month(), 'year': date_end.year()});
          this.reservationAction.newReservationObj = reserv;
          toRoom = +ev.target.dataset.hcalBedNum;
          needUpdate = true;
        }
      }

      if (needUpdate && reserv) {
        _.defer(function(r){ this._updateScroll(r._html); }.bind(this), reserv)

        var affectedReservations = [reserv].concat(this.getLinkedReservations(this.reservationAction.newReservationObj));
        for (var areserv of affectedReservations) {
          if (areserv !== reserv) {
            areserv.startDate = reserv.startDate.clone();
            areserv.endDate = reserv.endDate.clone();
          }

          if (areserv._html) {
            if (areserv.unusedZone) {
              areserv._html.style.visibility = 'hidden';
              continue;
            }
            _.defer(function(ro, r, tro){
              this._calcReservationCellLimits(
                r,
                r===ro?tro:undefined,
                !this.options.assistedMovement);
              this._updateDivReservation(r);

              if (!r._limits.isValid() || !this.checkReservationPlace(r) ||
                  (r.fixRooms && this.reservationAction.oldReservationObj.room.id != r.room.id) ||
                  (r.fixDays && !this.reservationAction.oldReservationObj.startDate.isSame(r.startDate, 'day'))) {
                r._html.classList.add('hcal-reservation-invalid');
              }
              else {
                r._html.classList.remove('hcal-reservation-invalid');
              }
            }.bind(this), reserv, areserv, toRoom);
          }
        }
      }
    }
  },

  onMainKeyUp: function(/*EventObject*/ev) {
    if (this.reservationAction.action === HotelCalendar.ACTION.SWAP || this.getSwapMode() !== HotelCalendar.MODE.NONE) {
      var needReset = false;
      if (ev.keyCode === 27) {
        this._dispatchEvent('hcalOnCancelSwapReservations');
        needReset = true;
      }
      else if (ev.keyCode === 13) {
        this._dispatchSwapReservations();
        needReset = true;
      }
      else if (ev.keyCode === 17 && this.getSwapMode() === HotelCalendar.MODE.SWAP_FROM) {
        this.setSwapMode(HotelCalendar.MODE.SWAP_TO);
      }

      if (needReset) {
        this._reset_action_reservation();
        this._updateHighlightSwapReservations();
        this._modeSwap = HotelCalendar.MODE.NONE;
      }
    }
  },

  onMainKeyDown: function(/*EventObject*/ev) {
    if (this.reservationAction.action === HotelCalendar.ACTION.SWAP || this.getSwapMode() !== HotelCalendar.MODE.NONE) {
      if (ev.keyCode === 17 && this.getSwapMode() === HotelCalendar.MODE.SWAP_TO) {
        this.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
      }
    }
  },

  onMainMouseUp: function(/*EventObject*/ev) {
    if (this._lazyModeReservationsSelection) {
      clearTimeout(this._lazyModeReservationsSelection);
      this._lazyModeReservationsSelection = false;
    }
    _.defer(function(ev){
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
            if (r._html) {
              hasInvalidLink = !hasInvalidLink && r._html.classList.contains('hcal-reservation-invalid');
              r._html.classList.remove('hcal-reservation-action');
              r._html.classList.remove('hcal-reservation-invalid');
            }
          }

          if (this.reservationAction.oldReservationObj && this.reservationAction.newReservationObj) {
            if (!this.options.allowInvalidActions && (reservDiv.classList.contains('hcal-reservation-invalid') || hasInvalidLink)) {
              this.replaceReservation(this.reservationAction.newReservationObj, this.reservationAction.oldReservationObj);
            } else {
              var oldReservation = this.reservationAction.oldReservationObj;
              var newReservation = this.reservationAction.newReservationObj;
              // Calc Old Reservation Price
              var oldDiff = this.getDateDiffDays(oldReservation.startDate, oldReservation.endDate);
              var oldPrice = 0.0
              for (var e=0; e<oldDiff; e++) {
                var ndate = oldReservation.startDate.clone().add(e, 'd');
                oldPrice += this.getRoomPrice(oldReservation.room, ndate);
              }
              // Calc New Reservation Price
              var newDiff = this.getDateDiffDays(newReservation.startDate, newReservation.endDate);
              var newPrice = 0.0
              for (var e=0; e<newDiff; e++) {
                var ndate = newReservation.startDate.clone().add(e, 'd');
                newPrice += this.getRoomPrice(newReservation.room, ndate);
              }

              this._dispatchEvent(
                'hcalOnChangeReservation',
                {
                  'oldReserv': oldReservation,
                  'newReserv': newReservation,
                  'oldPrice': oldPrice,
                  'newPrice': newPrice
                });
              _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
            }
            reservDiv.classList.remove('hcal-reservation-invalid');
          } else {
            this._dispatchEvent(
              'hcalOnClickReservation',
              {
                'event': ev,
                'reservationDiv': reservDiv,
                'reservationObj': reserv
              });
          }

          this._reset_action_reservation();
      }
      this._resetCellSelection();
      this._updateCellSelection();
    }.bind(this), ev);
  },

  onMainResize: function(/*EventObject*/ev) {
    _.defer(function(){
      this._updateReservations();
    }.bind(this));
  },

  onClickSelectorDate: function(/*EventObject*/ev, /*HTMLObject*/elm) {
      var $this = this;
      function setSelectorDate(elm) {
        var new_date = moment(elm.value, HotelCalendar.DATE_FORMAT_SHORT_);
        var span = document.createElement('span');
        span.addEventListener('click', function(ev){ $this.onClickSelectorDate(ev, elm); }, false);
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
      }, false);
      input.addEventListener('blur', function(ev){ setSelectorDate(this); }, false);
      elm.parentNode.insertBefore(input, elm);
      elm.parentNode.removeChild(elm);
      input.focus();
  },

  //==== COLOR FUNCTIONS (RANGE: 0.0|1.0)
  _intToRgb: function(/*Int*/RGBint) {
    return [(RGBint >> 16) & 255, (RGBint >> 8) & 255, RGBint & 255];
  },

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

/** CONSTANTS **/
HotelCalendar.DOMAIN = { NONE: -1, RESERVATIONS: 0, ROOMS: 1 };
HotelCalendar.ACTION = { NONE: -1, MOVE_ALL: 0, MOVE_LEFT: 1, MOVE_RIGHT: 2, SWAP: 3 };
HotelCalendar.MODE = { NONE: -1, SWAP_FROM: 0, SWAP_TO: 1 };
HotelCalendar.DATE_FORMAT_SHORT_ = 'DD/MM/YYYY';
HotelCalendar.DATE_FORMAT_LONG_ = HotelCalendar.DATE_FORMAT_SHORT_ + ' HH:mm:ss';
/** STATIC METHODS **/
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
  this.overbooking = false;

  this._html = false;
  this._active = true;
  this._userData = {};
}
HRoom.prototype = {
  clearUserData: function() { this._userData = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this._userData;
    }
    return key in this._userData && this._userData[key] || null;
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HRoom][setUserData] Invalid Data! Need be a object!");
    } else {
      this._userData = _.extend(this._userData, data);
    }
  },
  clone: function() {
    var nroom = new HRoom(
        this.id,
        this.number, // Name
        this.capacity, // Capacity
        this.type, // Category
        this.shared, // Shared Room
        this.price  // Price
    );
    nroom.overbooking = this.overbooking;
    nroom._html = this._html;
    nroom._active = this._active;
    nroom.addUserData(this.getUserData());
    return nroom;
  }
};

/** RESERVATION OBJECT **/
function HReservation(/*Dictionary*/rValues) {
  if (typeof rValues.room === 'undefined') {
    delete this;
    console.warn("[Hotel Calendar][HReservation] room can't be empty!");
    return;
  }

  this.id = rValues.id;
  this.room = rValues.room;
  this.adults = rValues.adults || 1;
  this.childrens = rValues.childrens || 0;
  this.title = rValues.title || '';
  this.startDate = rValues.startDate || null;
  this.endDate = rValues.endDate || null;
  this.color = rValues.color || '#000';
  this.colorText = rValues.colorText || '#FFF';
  this.readOnly = rValues.readOnly || false;
  this.fixRooms = rValues.fixRooms || false;
  this.fixDays = rValues.fixDays || false;
  this.unusedZone = rValues.unusedZone || false;
  this.linkedId = rValues.linkedId || -1;
  this.splitted = rValues.splitted || false;
  this.overbooking = rValues.overbooking || false;

  this._drawModes = ['hard-start', 'hard-end'];
  this._html = false;
  this._limits = new HLimit();
  this._beds = [];
  this._active = true;
  this._userData = {};
}
HReservation.prototype = {
  setRoom: function(/*HRoomObject*/room) { this.room = room; },
  setStartDate: function(/*String,MomentObject*/date) { this.startDate = HotelCalendar.toMomentUTC(date); },
  setEndDate: function(/*String,MomentObject*/date) { this.endDate = HotelCalendar.toMomentUTC(date); },

  clearUserData: function() { this._userData = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this._userData;
    }
    return key in this._userData && this._userData[key] || null;
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HReservation][setUserData] Invalid Data! Need be a object!");
    } else {
      this._userData = _.extend(this._userData, data);
    }
  },
  getTotalPersons: function() {
    return this.adults+this.childrens;
  },
  clone: function() {
    var nreserv = new HReservation({
      'id': this.id,
      'room': this.room,
      'adults': this.adults,
      'childrens': this.childrens,
      'title': this.title,
      'startDate': this.startDate.clone(),
      'endDate': this.endDate.clone(),
      'color': this.color,
      'colorText': this.colorText,
      'readOnly': this.readOnly,
      'fixRooms': this.fixRooms,
      'fixDays': this.fixDays,
      'unusedZone': this.unusedZone,
      'linkedId': this.linkedId,
      'splitted': this.splitted,
      'overbooking': this.overbooking
    });
    nreserv._beds = _.clone(this._beds);
    nreserv._html = this._html;
    nreserv._drawModes = _.clone(this._drawModes);
    nreserv._limits = this._limits.clone();
    nreserv._active = this._active;
    nreserv.addUserData(this.getUserData());
    return nreserv;
  }
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
  },
  clone: function() {
    return new HLimit(this.left, this.right);
  }
};

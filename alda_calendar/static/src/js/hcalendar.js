"use strict";
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


/***/ 
function HotelCalendar(/*String*/querySelector, /*Dictionary*/options, /*List*/reservations, /*HTMLObject*/_base) {
	if (window === this) {
		return new HotelCalendar(querySelector, options, reservations);
	}
	
	this.$base = (typeof _base === 'undefined')?document:_base;
	
	if (typeof querySelector === 'string') {		
		this.e = this.$base.querySelector(querySelector);
		if (!this.e) { 
			return false; 
		}
	} else if(typeof querySelector == 'object') {
		this.e = querySelector;
	} else {
		return {
			Version: '0.0.1a',
			Author: "Alexandre Díaz",
			Created: "20/04/2017",
			Updated: ""
		};
	}
	
	var $this = this;
	
	/** Options **/
	if (!options) { options = {}; }
	this.options = {
		startDate: moment(options.startDate || new Date()).subtract('1','d'),
		days: options.days || moment(options.startDate || new Date()).daysInMonth()+1,
		rooms: options.rooms || [],
		showPaginator: options.showPaginator || false,
		allowInvalidActions: options.allowInvalidActions || false,
		endOfWeek: options.endOfWeek || 6,
	};
	// Check correct values
	if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
		this.options.rooms = [];
		console.warn("[Hotel Calendar][init] Invalid Room definiton!");
	}
	
	/** Internal Values **/
	this.reservations = reservations || [];
	this.tableCreated = false;
	this.cellSelection = {start:false, end:false, current:false};
	this.numRooms = this.options.rooms.length;
	/** Constants **/
	this.ACTION = { NONE: -1, MOVE_ALL: 0, MOVE_LEFT: 1, MOVE_RIGHT: 2 };
	
	/***/
	this.reset_action_reservation_();
	if (!this.create_())
		return false;
	
	/** Main Events **/
	document.addEventListener('mouseup', this.onMainMouseUp.bind(this), false);
	window.addEventListener('resize', this.onMainResize.bind(this), false);
	this.etable.addEventListener('mousemove', this.onMainMouseMove.bind(this), false);
	
	return this;
}

HotelCalendar.prototype = {
	/** PUBLIC MEMBERS **/
	addEventListener: function(/*String*/event, /*Function*/callback) {
		this.e.addEventListener(event, callback);
	},
	
	//==== CALENDAR
	setStartDate(/*String,MomentObject*/date) {
		var curDate = this.options.startDate;
		if (moment.isMoment(date)) {
			this.options.startDate = date.subtract('1','d');
		} else if (typeof date === 'string'){
			this.options.startDate = moment(date).subtract('1','d');
		} else {
			console.warn("[Hotel Calendar][setStartDate] Invalid date format!");
			return;
		}
		
		this.e.dispatchEvent(new CustomEvent(
				'hcOnChangeDate',
				{'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));
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
	
	//==== RESERVATIONS
	clearReservationDivs: function() {
		var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
		for (var i=reservs.length; i>0; this.e.removeChild(reservs[--i]));
	},
	
	getReservation: function(id) {
		return this.reservations[id];
	},
	
	getReservationDiv: function(/*HReservationObject*/reservationObj) {
		var reservDivs = this.e.querySelectorAll('.hcal-reservation') || [];
		for (var rdiv of reservDivs) {
			var reservObj = this.reservations[rdiv.dataset.hcalReservationId];
			if (reservationObj === reservObj) {
				return rdiv;
			}
		}
		return null;
	},
	
	setReservations: function(/*List*/reservations) {
		this.reservations = reservations || [];
		if (this.reservations.length > 0) {
			if (!(this.reservations[0] instanceof HReservation)) {
				console.warn("[HotelCalendar][setReservations] Invalid Reservation definition!");
				this.reservations = [];
			} else {
				this.updateReservations_();
			}
		}
	},
	
	getReservationsByDay: function(/*String,MomentObject*/day, /*Int*/nroom, /*Int*/nbed) {
		var $this = this;
		var day = HotelCalendar.toMoment(day);
		if (!day) {
			return false;
		}
		
		var reservs = [];
		this.reservations.forEach(function(itemReserv, indexReserv){
			if (day.isBetween(itemReserv.startDate, itemReserv.endDate)
				&& (typeof nroom === 'undefined' || itemReserv.room.number == nroom)
				&& (typeof nbed === 'undefined' || itemReserv.beds_.includes(nbed))) {
				reservs.push(itemReserv);
			}
		});
		
		return reservs;
	},
	
	getReservationCellLimits: function(/*HReservationObject*/reservation, /*Int*/nbed, /*Bool*/notCheck) {
		var limits = new HLimit();
		var diff_date = reservation.endDate.diff(reservation.startDate, 'days');
		var rpersons = reservation.room.shared?reservation.room.capacity:1;
		var cellFound = false;
		var cellStartType = '';
		var cellEndType = '';
		
		// Search Initial Cell
		var bedNum = 0;
		if (typeof nbed === 'undefined') {
			bedNum = reservation.beds_.length?reservation.beds_[0]:0;
		} else {
			bedNum = nbed;
		}

		for (; bedNum<rpersons; bedNum++) {
			var cell = this.getCell(reservation.startDate, 
					reservation.room.type,
					reservation.room.number, 
					bedNum);
			if (!cell) {
				var date = reservation.startDate.clone();
				for (var i=0; i<=diff_date; i++) {
					cell = this.getCell(
						date.add(1, 'd'), 
						reservation.room.type, 
						reservation.room.number, 
						bedNum);
					if (cell) {
						cellStartType = 'soft-start';
						cellFound = true;
						break;
					}
				}
			} else {
				cellStartType = 'hard-start';
				cellFound = true;
			}
			
			if (cellFound) {
				limits.left = cell;
				break;
			}
		}
		
		// More Beds?
		var reservPersons = reservation.adults+reservation.childrens;
		if (reservation.room.shared && reservPersons > 1 && bedNum+reservPersons <= rpersons) { 
			++bedNum;
		}
		
		// Search End Cell
		cellFound = false;
		for (; bedNum<=rpersons; bedNum++) {
			var cell = this.getCell(reservation.endDate, 
					reservation.room.type,
					reservation.room.number, 
					bedNum);
			if (!cell) {
				var date = reservation.endDate.clone();
				for (var i=0; i<=diff_date; i++) {
					cell = this.getCell(
						date.subtract(1, 'd'), 
						reservation.room.type, 
						reservation.room.number, 
						bedNum);
					if (cell) {
						cellEndType = 'soft-end';
						cellFound = true;
						break;
					}
				}
			} else {
				cellEndType = 'hard-end';
				cellFound = true;
			}
			
			if (cellFound) {
				limits.right = cell;
				break;
			}
		}
		
		// Exists other reservation in the same place?
		if (!notCheck && limits.isValid()) {
			var diff_date = limits.getRightDate().diff(limits.getLeftDate(), 'days');
			var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
			var parentRow = document.querySelector(`#${limits.left.dataset.hcalParentCell}`);
			var date = HotelCalendar.toMoment(parentRow.dataset.hcalDate).subtract(1, 'd');
			for (var i=0; i<=diff_date; i++) {
				date.add(1, 'd');
				for (var b=0; b<=numBeds; b++) {
					var reservs = this.getReservationsByDay(date, reservation.room.number, +limits.left.dataset.hcalBedNum+b);
					reservs = _.reject(reservs, function(item){ return item===reservation; });
					if (reservs.length && !this.sameSimpleDate_(reservs[0].endDate, date)) {
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
			var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
			if (parentRow && room && room.type == type && room.number == number) {
				return elms[i];
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
		var start_date = limits.getLeftDate();
		var end_date = limits.getRightDate();
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
						+limits.left.dataset.hcalBedNum+nbed
					);
				if (cell) {
					cells.push(cell);
				}
			}
		}
		return cells;
	},
	
	//==== ROOMS
	getDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
		var reservs = this.getReservationsByDay(day);
		var nreservs = [];
		reservs.forEach(function(itemReserv, indexReserv){
			if (itemReserv.room.type === room_type) {
				nreservs.push(itemReserv);
			}
		});
		return nreservs;
	},
	
	getRoomsByType: function(/*String*/type) {
		var $this = this;
		rooms = [];
		this.options.rooms.forEach(function(itemRoom, indexRoom){
			if (itemRoom.type === type)
				rooms.push(itemRoom);
		});
		return rooms;
	},
	
	getRoomTypes: function() {
		var $this = this;
		var room_types = [];
		this.options.rooms.forEach(function(itemRoom, indexRoom){
			room_types.push(itemRoom.type);
		});
		return Array.from(new Set(room_types));
	},
	
	getRoom: function(/*String*/id) {
		var room = null;
		this.options.rooms.forEach(function(itemRoom, indexRoom){
			if (itemRoom.id == id) {
				room = itemRoom;
				return;
			}
		});
		return room;
	},
	
	//==== DETAIL CALCS
	calcDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
		var day = HotelCalendar.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getDayRoomTypeReservations(day, room_type);
		var num_rooms = this.getRoomsByType(room_type).length;
		return Math.round(num_rooms-reservs.length);
	},
	
	calcReservationOccupation: function(/*String,MomentObject*/day) {
		var day = HotelCalendar.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getReservationsByDay(day);
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
				if ($this.isLeftButtonPressed_(ev)) {
					var reserv = null;
					var toRoom = undefined;
					var needUpdate = false;
					var date_cell = HotelCalendar.toMoment(document.querySelector(`#${this.dataset.hcalParentCell}`).dataset.hcalDate);
					if (!$this.reservationAction.reservation) {
						if (!$this.cellSelection.start) {
							$this.cellSelection.start = this;
						} else if ($this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow &&
								$this.cellSelection.start.dataset.hcalBedNum === this.dataset.hcalBedNum) {
							$this.cellSelection.current = this;
						}
						$this.updateCellSelection_();
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_RIGHT) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						if (!date_cell.isAfter(reserv.startDate)) {
							date_cell = reserv.startDate.clone().add(1, 'd');
						}
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						reserv.endDate = date_cell;
						$this.reservationAction.newReservationObj = reserv;
						needUpdate = true;
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_LEFT) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						if (!date_cell.isBefore(reserv.endDate)) {
							date_cell = reserv.endDate.clone().subtract(1, 'd');
						}
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						reserv.startDate = date_cell;
						$this.reservationAction.newReservationObj = reserv;
						needUpdate = true;
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_ALL) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						var diff_date = reserv.endDate.diff(reserv.startDate, 'days');
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						var parentRow = $this.$base.querySelector(`#${this.dataset.hcalParentRow}`);
						var room = $this.getRoom(parentRow.dataset.hcalRoomObjId);
						reserv.room = room;
						reserv.startDate = date_cell;
						reserv.endDate = date_cell.clone().add(diff_date, 'd');
						$this.reservationAction.newReservationObj = reserv;
						toRoom = +this.dataset.hcalBedNum;
						needUpdate = true;
					}
					
					if (needUpdate) {
						var linkedReservations = $this.getLinkedReservations($this.reservationAction.newReservationObj);
						linkedReservations.push(reserv);
						
						linkedReservations.forEach(function(itemLinkedReservations, indexLinkedReservations){
							if (itemLinkedReservations!==reserv) {
								itemLinkedReservations.startDate = reserv.startDate;
								itemLinkedReservations.endDate = reserv.endDate;
							}
							
							var reservationDiv = $this.getReservationDiv(itemLinkedReservations);
							var limits = $this.getReservationCellLimits(itemLinkedReservations, itemLinkedReservations===reserv?toRoom:undefined, true);
							$this.updateDivReservation_(reservationDiv, limits);
							if (!$this.checkReservationPlace(itemLinkedReservations) || !limits) {
								reservationDiv.classList.add('hcal-reservation-invalid');
							} else {
								reservationDiv.classList.remove('hcal-reservation-invalid');
							}
						});
					}
				}
			}, false);
			cell.addEventListener('mousedown', function(ev){
				$this.cellSelection.start = $this.cellSelection.current = this;
				$this.cellSelection.end = false;
				$this.updateCellSelection_();
			}, false);
			cell.addEventListener('mouseup', function(ev){
				if ($this.cellSelection.start && $this.cellSelection.start != this && $this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow &&
						$this.cellSelection.start.dataset.hcalBedNum === this.dataset.hcalBedNum) {
					$this.cellSelection.end = this;
					$this.updateCellSelection_();
					
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
			var $this = this;
			var keys = Object.keys(this.options.rooms);
			
			this.options.rooms.forEach(function(itemRoom, indexRoom){
				rooms[itemRoom.number] = [$this.toAbbreviation(itemRoom.type), itemRoom.capacity];
			});
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
		var now = moment(new Date(), HotelCalendar.DATE_FORMAT_SHORT_);
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_);
			cell.innerHTML = `${dd.format('D')}<br/>${dd.format('ddd')}`;
			cell.setAttribute('title', dd.format('dddd'))
			var day = +dd.format('D');
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
				cur_month = dd.format('MMMM');
				months[cur_month] = {};
				months[cur_month].year = dd.format('YYYY');
				months[cur_month].colspan = 0;
			}
			if (this.sameSimpleDate_(dd, now)) {
				cell.classList.add('hcal-cell-current-day');
			} else if (dd.format('e') == 6) {
				cell.classList.add('hcal-cell-end-week');
			}
			++months[cur_month].colspan;
		}
		// Render Months
		var month_keys = Object.keys(months);
		month_keys.forEach(function(itemMonth, indexMonth){
			var cell_month = row_init.insertCell();
			cell_month.setAttribute('colspan', months[itemMonth].colspan);
			cell_month.innerText = itemMonth+' '+months[itemMonth].year;
			cell_month.classList.add('hcal-cell-month');
			cell_month.classList.add('btn-hcal');
			cell_month.classList.add('btn-hcal-3d');
		});

		/** ROOM LINES **/
		var tbody = document.createElement("tbody");
		this.etable.appendChild(tbody);
		this.options.rooms.forEach(function(itemRoom, indexRoom){
			// Room Number
			row = tbody.insertRow();
			row.setAttribute('id', `ROW_${itemRoom.number}_${itemRoom.type}_${indexRoom}`);
			row.dataset.hcalRoomObjId = itemRoom.id;
			row.classList.add('hcal-row-room-type-group-item');
			cell = row.insertCell();
			cell.textContent = itemRoom.number;
			cell.classList.add('hcal-cell-room-type-group-item');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell = row.insertCell();
			cell.textContent = $this.toAbbreviation(itemRoom.type);
			cell.classList.add('hcal-cell-room-type-group-item');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-flat');
			for (var i=0; i<$this.options.days; i++) {
				var dd = $this.options.startDate.clone().add(i,'d');
				cell = row.insertCell();
				cell.setAttribute('id', `${itemRoom.type}_${itemRoom.number}_${indexRoom}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
				cell.classList.add('hcal-cell-room-type-group-item-day');
				cell.dataset.hcalParentRow = row.getAttribute('id');
				cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
				// Generate Interactive Table
				cell.appendChild($this.generateTableDay_(cell));
				//cell.innerHTML = dd.format("DD");
				var day = +dd.format("D");
				if (day == 1) {
					cell.classList.add('hcal-cell-start-month');
				}
				if ($this.sameSimpleDate_(dd, now)) {
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
		var now = moment(new Date(), HotelCalendar.DATE_FORMAT_SHORT_);
		var thead = this.edtable.createTHead();
		var row = thead.insertRow();
		var cell = row.insertCell();
		cell.setAttribute('colspan', 2);
		cell.setAttribute('class', 'col-xs-1 col-lg-1');
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_);
			cell.innerHTML = `${dd.format('D')}<br/>${dd.format('ddd')}`;
			cell.setAttribute('title', dd.format("dddd"))
			var day = +dd.format("D");
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
			}
			if (this.sameSimpleDate_(dd, now)) {
				cell.classList.add('hcal-cell-current-day');
			} else if (dd.format('e') == 6) {
				cell.classList.add('hcal-cell-end-week');
			}
		}
		
		/** DETAIL LINES **/
		var tbody = document.createElement("tbody");
		this.edtable.appendChild(tbody);
		// Rooms Free Types
		if (this.options.rooms) {
			var room_types = this.getRoomTypes();
			room_types.forEach(function(itemRoomType, indexRoomType){
				row = tbody.insertRow();
				row.setAttribute('id', `ROW_DETAIL_FREE_TYPE_${itemRoomType}`);
				row.dataset.hcalRoomType = itemRoomType;
				row.classList.add('hcal-row-detail-room-free-type-group-item');
				cell = row.insertCell();
				cell.textContent = $this.toAbbreviation(itemRoomType);
				cell.classList.add('hcal-cell-detail-room-free-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', `${itemRoomType}_${indexRoomType}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
					cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
					cell.textContent = '0';
					var day = +dd.format("D");
					if (day == 1) {
						cell.classList.add('hcal-cell-start-month');
					}
					if ($this.sameSimpleDate_(dd, now)) {
						cell.classList.add('hcal-cell-current-day');
					} else if (dd.format('e') == 6) {
						cell.classList.add('hcal-cell-end-week');
					}
				}
			});
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
		for (var i=0; i<$this.options.days; i++) {
			var dd = $this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `CELL_DETAIL_TOTAL_FREE_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
			cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
			cell.textContent = '0';
			var day = +dd.format("D");
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
			}
			if ($this.sameSimpleDate_(dd, now)) {
				cell.classList.add('hcal-cell-current-day');
			} else if (dd.format('e') == 6) {
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
		for (var i=0; i<$this.options.days; i++) {
			var dd = $this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `CELL_DETAIL_PERC_OCCUP_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
			cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
			cell.textContent = '0';
			var day = +dd.format("D");
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
			}
			if ($this.sameSimpleDate_(dd, now)) {
				cell.classList.add('hcal-cell-current-day');
			} else if (dd.format('e') == 6) {
				cell.classList.add('hcal-cell-end-week');
			}
		}
		// Rooms Price Types
		if (this.options.rooms) {
			var room_types = this.getRoomTypes();
			room_types.forEach(function(itemRoomType, indexRoomType){
				row = tbody.insertRow();
				row.setAttribute('id', `ROW_DETAIL_PRICE_TYPE_${itemRoomType}`);
				row.dataset.hcalRoomType = itemRoomType;
				row.classList.add('hcal-row-detail-room-price-type-group-item');
				cell = row.insertCell();
				cell.textContent = $this.toAbbreviation(itemRoomType)+' €';
				cell.classList.add('hcal-cell-detail-room-price-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', `${itemRoomType}_${indexRoomType}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
					cell.classList.add('hcal-cell-detail-room-price-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
					cell.textContent = '0';
					var day = +dd.format("D");
					if (day == 1) {
						cell.classList.add('hcal-cell-start-month');
					}
					if ($this.sameSimpleDate_(dd, now)) {
						cell.classList.add('hcal-cell-current-day');
					} else if (dd.format('e') == 6) {
						cell.classList.add('hcal-cell-end-week');
					}
				}
			});
		}
		// Minimum Stay
		row = tbody.insertRow();
		row.setAttribute('id', "ROW_DETAIL_MIN_STAY");
		row.classList.add('hcal-row-detail-room-min-stay-group-item');
		cell = row.insertCell();
		cell.textContent = 'MIN. STAY';
		cell.classList.add('hcal-cell-detail-room-min-stay-group-item');
		cell.classList.add('btn-hcal');
		cell.classList.add('btn-hcal-flat');
		cell.setAttribute("colspan", "2");
		for (var i=0; i<$this.options.days; i++) {
			var dd = $this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `CELL_DETAIL_MIN_STAY_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_LEGACY_)}`);
			cell.classList.add('hcal-cell-detail-room-min-stay-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
			cell.textContent = '0';
			var day = +dd.format("D");
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
			}
			if ($this.sameSimpleDate_(dd, now)) {
				cell.classList.add('hcal-cell-current-day');
			} else if (dd.format('e') == 6) {
				cell.classList.add('hcal-cell-end-week');
			}
		}
	},
	
	//==== UPDATE FUNCTIONS
	updateView_: function() {
		this.create_table_reservation_days_();
		this.create_table_detail_days_();
		
		this.updateReservations_(); 
		//this.updateReservationOccupation_();
		//this.updateRoomTypeFreeRooms_();
		this.updateCellSelection_();
	},
	
	updateCellSelection_: function() {
		// Clear all
		var tables_td = this.etable.querySelectorAll('.hcal-table-day td');
		for (var i=0; i<tables_td.length; i++) {
			tables_td[i].classList.remove('hcal-cell-highlight');
		}
		// Highlight Selected
		if (this.cellSelection.current) {
			this.cellSelection.current.classList.add('hcal-cell-highlight');
		}
		// Highlight Range Cells
		var limits = new HLimit(this.cellSelection.start, 
								this.cellSelection.end?this.cellSelection.end:this.cellSelection.current);
		if (limits.isValid()) {
			var cells = this.getCells(limits);
			cells.forEach(function(itemCell, indexCell){
				itemCell.classList.add('hcal-cell-highlight');
			});
		}
	},
	
	updateDivReservation_: function(/*HTMLObject*/divRes, /*HLimitObject*/limits) {
		if (!limits || !limits.isValid()) {
			return;
		}
		
		var dateCellInit = limits.getLeftDate();
		var dateCellEnd = limits.getRightDate();
		var etableOffset = this.etable.getBoundingClientRect();
		
		var reserv = this.reservations[divRes.dataset.hcalReservationId];
		var numBeds = (+limits.right.dataset.hcalBedNum)-(+limits.left.dataset.hcalBedNum);
		reserv.beds_ = [];
		for (var i=0; i<=numBeds; reserv.beds_.push(+limits.left.dataset.hcalBedNum+i++));
		
		var boundsInit = limits.left.getBoundingClientRect();
		var boundsEnd = limits.right.getBoundingClientRect();

		divRes.style = {}; // FIXME: Reset Style. Good method?
		divRes.style.top = `${boundsInit.top-etableOffset.top}px`;
		var divHeight = (boundsEnd.bottom-etableOffset.top)-(boundsInit.top-etableOffset.top);
		divRes.style.height = `${divHeight}px`;
		divRes.style.lineHeight = `${divHeight-3}px`;
		divRes.style.fontSize = `${divHeight/2}px`;
		if (limits.left.dataset.hcalReservationCellType === 'soft-start' 
				|| (limits.isSame() && this.sameSimpleDate_(dateCellInit, this.options.startDate))) {
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
		} else if (limits.left.dataset.hcalReservationCellType !== 'soft-start' 
						&& !this.sameSimpleDate_(dateCellInit, this.options.startDate)) {
			divRes.style.width = `${boundsEnd.left-boundsInit.left}px`;
		}
	},
	
	swapReservation: function(/*HReservationObject*/reservationObj, /*HReservationObject*/newReservationObj) {
		var $this = this;
		var reservationDiv = this.getReservationDiv(reservationObj);
		if (!reservationDiv) {
			console.warn("[Hotel Calendar][updateReservation_] Invalid Reservation Object");
			return;
		}
		
		delete this.reservations[reservationDiv.dataset.hcalReservationId];
		this.reservations[reservationDiv.dataset.hcalReservationId] = newReservationObj;
		var limits = this.getReservationCellLimits(newReservationObj);
		this.updateDivReservation_(reservationDiv, limits);
		
		var linkedReservations = this.getLinkedReservations(newReservationObj);
		linkedReservations.forEach(function(itemLinkedReservation, indexLinkedReservation){
			itemLinkedReservation.startDate = newReservationObj.startDate;
			itemLinkedReservation.endDate = newReservationObj.endDate;
			
			var reservationDiv = $this.getReservationDiv(itemLinkedReservation);
			var limits = $this.getReservationCellLimits(itemLinkedReservation);
			$this.updateDivReservation_(reservationDiv, limits);
		});
	},
	
	getLinkedReservations: function(reservationObj) {
		return _.reject(this.reservations, function(item){ return item === reservationObj || item.id !== reservationObj.id; });
	},
	
	updateReservations_: function() {
		var $this = this;
		this.clearReservationDivs();
		
		this.reservations.forEach(function(itemReserv, indexReserv){
			var limits = $this.getReservationCellLimits(itemReserv);
			
			// Fill
			if (limits.isValid()) {
				var divRes = document.createElement('div');
				divRes.dataset.hcalReservationId = indexReserv;
				divRes.classList.add('hcal-reservation');
				divRes.classList.add('noselect');
				divRes.innerText = itemReserv.title;
				$this.updateDivReservation_(divRes, limits);
				$this.e.appendChild(divRes);
				
				var cells = $this.getCells(limits);
				cells.forEach(function(itemc, indexc){
					itemc.classList.add('hcal-cell-room-type-group-item-day-occupied');
					itemc.dataset.hcalReservationId = indexReserv;
				});
			}
		});
		
		this.assignReservationsEvents_();
	},
	
	assignReservationsEvents_: function() {
		var $this = this;
		var reservs = this.e.querySelectorAll('div.hcal-reservation');
		reservs.forEach(function(itemReserv, indexReserv) {
			var bounds = itemReserv.getBoundingClientRect();
			itemReserv.addEventListener('mousemove', function(ev){
				var posAction = $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY);
				if (posAction == $this.ACTION.MOVE_LEFT || posAction == $this.ACTION.MOVE_RIGHT) {
					itemReserv.style.cursor = "col-resize";
				} else {
					itemReserv.style.cursor = "pointer";
				}
			}, false);
			itemReserv.addEventListener('mousedown', function(ev){
				if (!$this.reservationAction.reservation && $this.isLeftButtonPressed_(ev)) {
					this.classList.add('hcal-reservation-action');
					$this.reservationAction = { 
						action: $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY),
						reservation: this
					};
					
					var reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
					var linkedReservations = $this.getLinkedReservations(reserv);
					linkedReservations.forEach(function(itemLinkedReservation, indexLinkedReservation){
						var reservationDiv = $this.getReservationDiv(itemLinkedReservation);
						reservationDiv.classList.add('hcal-reservation-action');
					});
				}
			}, false);
			itemReserv.addEventListener('contextmenu', function(ev){
				$this.e.dispatchEvent(new CustomEvent(
						'hcalOnContextMenuReservation', 
						{ 'detail': {
								'event': ev,
								'reservationDiv': this,
								'reservationObj': $this.reservations[this.dataset.hcalReservationId]
							}
						}));
				if(ev.preventDefault != undefined)
					ev.preventDefault();
				if(ev.stopPropagation != undefined)
					ev.stopPropagation();
				return false;
			}, false);
			itemReserv.addEventListener('mouseenter', function(ev){
				$this.e.dispatchEvent(new CustomEvent(
						'hcalOnMouseEnterReservation', 
						{ 'detail': {
								'event': ev,
								'reservationDiv': this,
								'reservationObj': $this.reservations[this.dataset.hcalReservationId]
							}
						}));
			}, false);
			itemReserv.addEventListener('mouseleave', function(ev){
				$this.e.dispatchEvent(new CustomEvent(
						'hcalOnMouseLeaveReservation', 
						{ 'detail': {
								'event': ev,
								'reservationDiv': this,
								'reservationObj': $this.reservations[this.dataset.hcalReservationId]
							}
						}));
			}, false);
		});
	},
	
	getRerservationPositionAction_: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
		var bounds = elm.getBoundingClientRect();
		if (posX <= 5) { return this.ACTION.MOVE_LEFT; }
		else if (posX >= bounds.width-10) { return this.ACTION.MOVE_RIGHT; }
		return this.ACTION.MOVE_ALL;
	},
	
	updateReservationOccupation_: function() {
		var cells = this.etable.querySelectorAll('td.hcal-cell-month-day-occupied');
		for (var i=0; i<cells.length; i++) {
			var parentCell = this.$base.querySelector(`#${cells[i].dataset.hcalParentCell}`);
			var cell_date = parentCell.dataset.hcalDate;
			var perOccup = this.calcReservationOccupation(cell_date);
			cells[i].innerText = perOccup+'%';
			cells[i].style.backgroundColor = this.generateColor_(perOccup, 100, 0.35, false, true);
		}
	},
	
	//==== HELPER FUNCTIONS
	sameSimpleDate_: function(/*MomentObject*/dateA, /*MomentObject*/dateB) {
		return dateA.isSame(dateB,'day') && dateA.isSame(dateB,'month') && dateA.isSame(dateB,'year');
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
		if (reservationObj.room.shared && reservationObj.beds_.length < reservationObj.adults+reservationObj.childrens) {
			return false;
		}

		var reservs = _.reject(this.reservations, function(item){ return reservationObj===item; });
		for (var i=0; i<reservs.length; i++) {
			var itemReservation = reservs[i];
			if ((reservationObj.room.number == itemReservation.room.number)
				&& (_.difference(reservationObj.beds_, itemReservation.beds_).length != reservationObj.beds_.length)
				&& (!this.sameSimpleDate_(reservationObj.startDate, itemReservation.endDate)) 
				&& (!this.sameSimpleDate_(reservationObj.endDate, itemReservation.startDate))
				&& (itemReservation.startDate.isBetween(reservationObj.startDate, reservationObj.endDate)
						|| itemReservation.endDate.isBetween(reservationObj.startDate, reservationObj.endDate)
						|| reservationObj.startDate.isSame(itemReservation.startDate)
								&& reservationObj.endDate.isSame(itemReservation.endDate))) {
				return false;
			}
		}

		return true;
	},
	
	//==== EVENT FUNCTIONS
	onMainMouseUp: function(/*EventObject*/ev) {
		if (this.reservationAction.reservation) {
			var $this = this;
			var reservDiv = this.reservationAction.reservation;
			reservDiv.classList.remove('hcal-reservation-action');
			
			var reserv = this.reservations[reservDiv.dataset.hcalReservationId];
			var linkedReservations = this.getLinkedReservations(reserv);
			linkedReservations.forEach(function(itemLinkedReservation, indexLinkedReservation){
				var reservationDiv = $this.getReservationDiv(itemLinkedReservation);
				reservationDiv.classList.remove('hcal-reservation-action');
				reservationDiv.classList.remove('hcal-reservation-invalid');
			});
			
			if (this.reservationAction.oldReservationObj && this.reservationAction.newReservationObj) {
				if (!this.options.allowInvalidActions && reservDiv.classList.contains('hcal-reservation-invalid')) {
					reservDiv.classList.remove('hcal-reservation-invalid');
					this.swapReservation(this.reservationAction.newReservationObj, this.reservationAction.oldReservationObj);
				} else {
					this.e.dispatchEvent(new CustomEvent(
						'hcalOnChangeReservation', 
						{ 'detail': {
								'old':this.reservationAction.oldReservationObj,
								'new':this.reservationAction.newReservationObj
							}
						}));
				}
			}
			this.reset_action_reservation_();
		}
	},
	
	onMainMouseMove: function(/*EventObject*/ev) {
		if (!this.reservationAction.reservation) {
			this.etable.style.cursor = "default";
		} else if (this.reservationAction.action == this.ACTION.MOVE_ALL) {
			this.etable.style.cursor = "move";
		} else {
			this.etable.style.cursor = "col-resize";
		}
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
				$this.setStartDate(moment(new Date()));
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
	
	//==== COLOR FUNCTIONS
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
HotelCalendar.DATE_FORMAT_SHORT_ = "DD/MM/YYYY";
HotelCalendar.DATE_FORMAT_SHORT_LEGACY_ = "DD_MM_YYYY";
HotelCalendar.toMoment = function(/*String,MomentObject*/date, /*String*/format) { 
	if (moment.isMoment(date)) {
		return date;
	} else if (typeof date === 'string' || date instanceof Date) {
		date = moment(date, typeof format==='undefined'?HotelCalendar.DATE_FORMAT_SHORT_:format);
		if (moment.isMoment(date)) {
			return date;
		}
	}
	console.warn('[Hotel Calendar][toMoment] Invalid date format!');
	return false;
}


/** ROOM OBJECT **/
function HRoom(/*Int*/id, /*String*/number, /*Int*/capacity, /*String*/type, /*Bool*/shared) {
	this.id = id || -1;
	this.number = number || -1;
	this.capacity = capacity || 1;
	this.type = type || '';
	this.shared = shared;
	
	this.userData_ = {};
}
HRoom.prototype = {
		clearUserData: function() { this.userData_ = {}; },
		getUserData: function(/*String*/key) { 
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
function HReservation(/*Int*/id, /*HRoomObject*/room, /*String*/title, /*Int*/adults, /*Int*/childrens, /*String,MomentObject*/startDate, /*String,MomentObject*/endDate) {
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
	
	this.beds_ = [];
	this.userData_ = {};
	
	if (typeof startDate !== 'undefined') { this.setStartDate(startDate); }
	else { this.startDate = ''; }
	if (typeof endDate !== 'undefined') { this.setEndDate(endDate); }
	else { this.endDate = ''; }
}
HReservation.prototype = {
	setStartDate: function(/*String,MomentObject*/date) { this.startDate = HotelCalendar.toMoment(date, null); },
	setEndDate: function(/*String,MomentObject*/date) { this.endDate = HotelCalendar.toMoment(date, null); },
	
	clearUserData: function() { this.userData_ = {}; },
	getUserData: function(/*String*/key) { 
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
};

/** LIMIT OBJECT **/
function HLimit(/*HTMLObject*/left, /*HMTLObject*/right) {
	this.left = left;
	this.right = right;
}
HLimit.prototype = {
	getLeftDate: function() {
		return HotelCalendar.toMoment(document.querySelector(`#${this.left.dataset.hcalParentCell}`).dataset.hcalDate);
	},
	getRightDate: function() {
		return HotelCalendar.toMoment(document.querySelector(`#${this.right.dataset.hcalParentCell}`).dataset.hcalDate);
	},
	isSame: function() {
		return this.left == this.right;
	},
	isValid: function() {
		return this.left && this.right;
	}
};

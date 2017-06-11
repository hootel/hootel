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

function HotelCalendar(/*String*/querySelector, /*Dictionary*/options, /*List*/pricelist, /*HTMLObject?*/_base) {
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
	
	/** Options **/
	if (!options) { options = {}; }
	this.options = {
		startDate: moment(options.startDate || new Date()).subtract('1','d'),
		days: options.days || moment(options.startDate || new Date()).daysInMonth()+1,
		rooms: options.rooms || [],
		showPaginator: options.showPaginator || false,
		allowInvalidActions: options.allowInvalidActions || false,
		assistedMovement: options.assistedMovement || false,
		endOfWeek: options.endOfWeek || 6,
	};
	// Check correct values
	if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
		this.options.rooms = [];
		console.warn("[Hotel Calendar][init] Invalid Room definiton!");
	}
	
	/** Internal Values **/
	this.isNRerservation = true;
	this.pricelist = pricelist || [];
	this.reservations = [];
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
	
	return this;
}

HotelCalendar.prototype = {
	/** PUBLIC MEMBERS **/
	addEventListener: function(/*String*/event, /*Function*/callback) {
		this.e.addEventListener(event, callback);
	},
	
	//==== CALENDAR
	setStartDate(/*String,MomentObject*/date, /*Int?*/days) {
		var curDate = this.options.startDate;
		if (moment.isMoment(date)) {
			this.options.startDate = date.subtract('1','d');
		} else if (typeof date === 'string'){
			this.options.startDate = moment(date).subtract('1','d');
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
		this.reservations = [];
		this.addReservations(reservations);
	},
	
	addReservations: function(/*List*/reservations) {
		if (reservations.length > 0 && !(reservations[0] instanceof HReservation)) {
			console.warn("[HotelCalendar][setReservations] Invalid Reservation definition!");
		} else {
			this.isNRerservation = true;
			this.reservations = this.reservations.concat(reservations);
			this.updateReservations_();
		}
	},
	
	getReservationsByDay: function(/*String,MomentObject*/day, /*Bool*/strict, /*Int?*/nroom, /*Int?*/nbed) {
		var day = HotelCalendar.toMoment(day);
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
		
		var bedNum = 0;
		if (typeof nbed === 'undefined') {
			bedNum = (reservation.beds_&&reservation.beds_.length)?reservation.beds_[0]:0;
		} else {
			bedNum = nbed;
		}
		
		var diff_date = reservation.endDate.startOf('day').diff(reservation.startDate.startOf('day'), 'days');
		var rpersons = reservation.room.shared?reservation.room.capacity:1;
		var cellFound = false;
		var cellStartType = '';
		var cellEndType = '';
		
		// Search Initial Cell
		var cell = this.getCell(reservation.startDate.startOf('day'), 
				reservation.room.type,
				reservation.room.number, 
				bedNum);
		if (!cell) {
			var date = reservation.startDate.startOf('day').clone();
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
		var cell = this.getCell(reservation.endDate.endOf('day'), 
				reservation.room.type,
				reservation.room.number, 
				bedNum);
		if (!cell) {
			var date = reservation.endDate.endOf('day').clone();
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
			var diff_date = limitRightDate.startOf('day').diff(limitLeftDate.endOf('day'), 'days');
			var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
			var parentRow = this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`);
			var date = HotelCalendar.toMoment(parentRow.dataset.hcalDate).startOf('day').subtract(1, 'd');
			for (var i=0; i<diff_date; i++) {
				date.add(1, 'd');
				for (var b=0; b<=numBeds; b++) {
					var reservs = this.getReservationsByDay(date, false, reservation.room.number, +limits.left.dataset.hcalBedNum+b);
					reservs = _.reject(reservs, function(item){ return item===reservation; });
					if (reservs.length && !reservs[0].endDate.isSame(date, 'day')) {
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
	
	//==== DETAIL CALCS
	calcDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
		var day = HotelCalendar.toMoment(day);
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
		var day = HotelCalendar.toMoment(day);
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
		var day = HotelCalendar.toMoment(day);
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
				if ($this.isLeftButtonPressed_(ev)) {
					var reserv = null;
					var toRoom = undefined;
					var needUpdate = false;
					var date_cell = HotelCalendar.toMoment($this.etable.querySelector(`#${this.dataset.hcalParentCell}`).dataset.hcalDate);
					if (!$this.reservationAction.reservation) {
						if (!$this.cellSelection.start) {
							$this.cellSelection.start = this;
						} else if ($this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow) {
							$this.cellSelection.current = this;
						}
						$this.updateCellSelection_();
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_RIGHT) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						if (!date_cell.isAfter(reserv.startDate.startOf('day'))) {
							date_cell = reserv.startDate.startOf('day').clone().add(1, 'd');
						}
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						reserv.endDate = moment(date_cell.format('DD-MM-YYYY')+' '+reserv.endDate.format('HH:mm:ss'), 'DD-MM-YYYY HH:mm:ss');
						$this.reservationAction.newReservationObj = reserv;
						needUpdate = true;
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_LEFT) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						var ndate = reserv.endDate.endOf('day').clone().subtract(1, 'd');
						if (!date_cell.isBefore(ndate)) {
							date_cell = ndate;
						}
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						reserv.startDate = moment(date_cell.format('DD-MM-YYYY')+' '+reserv.startDate.format('HH:mm:ss'), 'DD-MM-YYYY HH:mm:ss');
						$this.reservationAction.newReservationObj = reserv;
						needUpdate = true;
					} else if ($this.reservationAction.action == $this.ACTION.MOVE_ALL) {
						reserv = $this.reservations[$this.reservationAction.reservation.dataset.hcalReservationId];
						if (!$this.reservationAction.oldReservationObj) {
							$this.reservationAction.oldReservationObj = _.clone(reserv);
						}
						var parentRow = $this.$base.querySelector(`#${this.dataset.hcalParentRow}`);
						var room = $this.getRoom(parentRow.dataset.hcalRoomObjId);
						reserv.room = room;
						var diff_date = reserv.endDate.startOf('day').diff(reserv.startDate.startOf('day'), 'days');
						reserv.startDate = moment(date_cell.format('DD-MM-YYYY')+' '+reserv.startDate.format('HH:mm:ss'), 'DD-MM-YYYY HH:mm:ss');
						var date_end = reserv.startDate.clone().add(diff_date, 'd');
						reserv.endDate = moment(date_end.format('DD-MM-YYYY')+' '+reserv.endDate.format('HH:mm:ss'), 'DD-MM-YYYY HH:mm:ss');
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
				$this.resetCellSelection_();
				$this.updateCellSelection_();
			}, false);
		}
		
		return table;
	},
	
	get_normalized_rooms_: function() {
		var rooms = {};
		if (this.options.rooms) {
			var keys = Object.keys(this.options.rooms);
			
			for (var r of this.options.rooms) {
				rooms[r.number] = [this.toAbbreviation(r.type), r.capacity];
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
		var now = moment().local();
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
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
				cell.setAttribute('id', `${itemRoom.type}_${itemRoom.number}_${indexRoom}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
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
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `hday_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
			cell.innerHTML = `${dd.format('D')}<br/>${dd.format('ddd')}`;
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
				row.setAttribute('id', `ROW_DETAIL_FREE_TYPE_${rt}`);
				row.dataset.hcalRoomType = rt;
				row.classList.add('hcal-row-detail-room-free-type-group-item');
				cell = row.insertCell();
				cell.textContent = $this.toAbbreviation(rt);
				cell.classList.add('hcal-cell-detail-room-free-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', `CELL_FREE_${rt}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
					cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
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
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `CELL_DETAIL_TOTAL_FREE_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
			cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
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
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', `CELL_DETAIL_PERC_OCCUP_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
			cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
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
		// Rooms Price Types
		if (this.options.rooms) {
			var room_types = this.getRoomTypes();
			for (var rt of room_types) {
				row = tbody.insertRow();
				row.setAttribute('id', `ROW_DETAIL_PRICE_TYPE_${rt}`);
				row.dataset.hcalRoomType = rt;
				row.classList.add('hcal-row-detail-room-price-type-group-item');
				cell = row.insertCell();
				cell.textContent = $this.toAbbreviation(rt)+' €';
				cell.classList.add('hcal-cell-detail-room-price-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', `CELL_PRICE_${rt}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
					cell.classList.add('hcal-cell-detail-room-price-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
					var day = +dd.format("D");
					if (day == 1) {
						cell.classList.add('hcal-cell-start-month');
					}
					if (dd.isSame(now, 'day')) {
						cell.classList.add('hcal-cell-current-day');
					} else if (dd.format('e') == $this.options.endOfWeek) {
						cell.classList.add('hcal-cell-end-week');
					}
					
					//console.log("MIRA EEE");
					//console.log(dd.format("YYYY-MM-DD"));
					var dd_fmrt = dd.startOf('day').utc().format("YYYY-MM-DD"); // Local -> UTC
					//console.log(dd_fmrt);
					var input = document.createElement('input');
					input.classList.add('input-price');
					input.setAttribute("type", "text");
					input.readonly = true;
					input.value = _.has($this.pricelist[rt], dd_fmrt)?$this.pricelist[rt][dd_fmrt]:'...';
					input.dataset.ovalue = input.value;
					input.addEventListener('change', function(ev){
						var parentRow = $this.edtable.querySelector(`#${this.parentNode.dataset.hcalParentRow}`);
						var cdate = moment(this.parentNode.dataset.hcalDate, HotelCalendar.DATE_FORMAT_SHORT_).utc();
						$this.e.dispatchEvent(new CustomEvent(
							'hcalOnChangeRoomTypePrice', 
							{ 'detail': {
									'room_type': parentRow.dataset.hcalRoomType,
									'date': cdate,
									'price': this.value,
									'old_price': this.dataset.ovalue,
								}
							}));
						this.dataset.ovalue = this.value;
					}, false);
					cell.appendChild(input);
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
	
	//==== SELECTION
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
			// Normalize
			// TODO: Multi-Directional Selection. Now only support normal or inverse.
			var limitLeftDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
			var limitRightDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
			if (limitLeftDate.isAfter(limitRightDate)) {
				limits.swap();
			}
			var cells = this.getCells(limits);
			for (var c of cells) {
				c.classList.add('hcal-cell-highlight');
			}
		}
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
		
		var reserv = this.reservations[divRes.dataset.hcalReservationId];
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
		if (fontHeight > 16)
			fontHeight = 16;
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
		
		delete this.reservations[reservationDiv.dataset.hcalReservationId];
		this.reservations[reservationDiv.dataset.hcalReservationId] = newReservationObj;
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
		var dd = HotelCalendar.toMoment(date);
		var cell_input = this.edtable.querySelector(`#CELL_PRICE_${room_type}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)} input`);
		cell_input.value = price;
	},
	
	getLinkedReservations: function(/*HReservationObject*/reservationObj) {
		return _.reject(this.reservations, function(item){ return item === reservationObj || item.id !== reservationObj.id; });
	},
	
	updateReservations_: function() {
		var $this = this;
		this.clearReservationDivs();
		
		var errors = [];
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
				for (var c of cells) {
					c.classList.add('hcal-cell-room-type-group-item-day-occupied');
					c.dataset.hcalReservationId = indexReserv;
				}
			} else {
				console.warn(`[Hotel Calendar][updateReservations_] Can't place reservation ID@${itemReserv.id}`);
				errors.push(itemReserv);
			}
		});
		
		this.assignReservationsEvents_();
		
		this.updateReservationOccupation_();
		this.updatePriceList_();
		//this.updateRoomTypeFreeRooms_();
		
		if (errors.length && this.isNRerservation) {
			alert("[Hotel Calendar]\nWARNING: Can't show all reservations!\n\nSee debugger for more details.");
		}
		this.isNRerservation = false;
	},
	
	assignReservationsEvents_: function() {
		var $this = this;
		var reservDivs = this.e.querySelectorAll('div.hcal-reservation');
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

					var reserv = $this.reservations[this.dataset.hcalReservationId];
					if (reserv.readOnly) {
						$this.reservationAction.action = this.ACTION.NONE;
						var reservationDiv = $this.getReservationDiv(reserv);
						reservationDiv.classList.add('hcal-reservation-action-cancel');
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
			rdiv.addEventListener('contextmenu', function(ev){
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
			rdiv.addEventListener('mouseenter', function(ev){
				$this.e.dispatchEvent(new CustomEvent(
						'hcalOnMouseEnterReservation', 
						{ 'detail': {
								'event': ev,
								'reservationDiv': this,
								'reservationObj': $this.reservations[this.dataset.hcalReservationId]
							}
						}));
			}, false);
			rdiv.addEventListener('mouseleave', function(ev){
				$this.e.dispatchEvent(new CustomEvent(
						'hcalOnMouseLeaveReservation', 
						{ 'detail': {
								'event': ev,
								'reservationDiv': this,
								'reservationObj': $this.reservations[this.dataset.hcalReservationId]
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
	
	updatePriceList_: function() {
		var keys = _.keys(this.pricelist);
		for (var k of keys) {
			var pr = this.pricelist[k];
			var pr_keys = _.keys(this.pricelist[k]);
			for (var prk of pr_keys) {
				var dd = moment(prk);
				var price = this.pricelist[k][prk];
				var cell = this.edtable.querySelector(`#CELL_PRICE_${k}_${dd.format(HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_)}`);
				if (cell) {
					cell.firstChild.value = price;
				}
			}
		}
	},
	
	//==== HELPER FUNCTIONS	
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
			reservDiv.classList.remove('hcal-reservation-action-cancel');
			
			var rdivs = this.e.querySelectorAll('div.hcal-reservation.hcal-reservation-foreground');
			for (var rd of rdivs) { rd.classList.remove('hcal-reservation-foreground'); }
			
			var reserv = this.reservations[reservDiv.dataset.hcalReservationId];
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
			}
			this.reset_action_reservation_();
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
HotelCalendar.DATE_FORMAT_LONG_ = "DD/MM/YYYY HH:mm:ss";
HotelCalendar.DATE_FORMAT_SHORT_ = "DD/MM/YYYY";
HotelCalendar.DATE_FORMAT_SHORT_SANITIZED_ = "DD_MM_YYYY";
HotelCalendar.toMoment = function(/*String,MomentObject*/date, /*String*/format) { 
	if (moment.isMoment(date)) {
		return date;
	} else if (typeof date === 'string' || date instanceof Date) {
		date = moment(date, typeof format==='undefined'?HotelCalendar.DATE_FORMAT_LONG_:format);
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
function HReservation(/*Int*/id, /*HRoomObject*/room, /*String?*/title, /*Int?*/adults, /*Int?*/childrens, /*String,MomentObject??*/startDate, /*String,MomentObject??*/endDate, /*String?*/color, /*Boolean?*/readOnly) {
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
	this.startDate = null; 	// Local Time
	this.endDate = null;	// Local Time
	this.color = color || '#000';
	this.readOnly = readOnly || false;
	
	this.beds_ = [];
	this.userData_ = {};
	
	if (typeof startDate !== 'undefined') { this.setStartDate(startDate); }
	if (typeof endDate !== 'undefined') { this.setEndDate(endDate); }
}
HReservation.prototype = {
	setStartDate: function(/*String,MomentObject*/date) { this.startDate = HotelCalendar.toMoment(date); },
	setEndDate: function(/*String,MomentObject*/date) { this.endDate = HotelCalendar.toMoment(date); },
	
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

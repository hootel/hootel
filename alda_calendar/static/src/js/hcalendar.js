"use strict";
/*
 * Hotel Calendar JS v0.0.1a - 2017
 * GNU Public License
 * Aloxa Solucions S.L. <info@aloxa.eu>
 *     Alexandre Díaz <alex@aloxa.eu>
 */


/** EXTEND BASE OBJECTS: HELPER FUNCTIONS **/
if (!String.prototype.toAbbreviation) {
	String.prototype.toAbbreviation = function(max) {
		return this.replace(/[aeiouáéíóúäëïöü]/gi,'').toUpperCase().substr(0, max || 3);
	}
}


/***/ 
function HotelCalendar(querySelector, options, reservations, _base) {
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
	
	/** Main Events **/
	document.addEventListener('mouseup', this.onMainMouseUp.bind(this), false);
	
	/** Options **/
	if (!options) { options = {}; }
	this.options = {
		startDate: moment(options.startDate || new Date(), this.DATE_FORMAT_SHORT_).subtract('1','d'),
		days: options.days || moment(options.startDate || new Date(), this.DATE_FORMAT_SHORT_).daysInMonth()+1,
		rooms: options.rooms || {},
		showPaginator: options.showPaginator || false,
	};
	
	/** Internal Values **/
	this.reservations = reservations || [];
	this.tableCreated = false;
	this.cellSelection = {start:false, end:false, current:false};
	this.numRooms = this.options.rooms.length;
	
	/***/
	if (!this.create_())
		return false;
	return this;
};

HotelCalendar.prototype = {
	/** PUBLIC MEMBERS **/
	addEventListener: function(event, callback) {
		this.e.addEventListener(event, callback);
	},
	
	//==== CALENDAR
	setStartDate(date) {
		if (moment.isMoment(date)) {
			this.options.startDate = date.subtract('1','d');
		} else if (typeof date === 'string'){
			this.options.startDate = moment(date, this.DATE_FORMAT_SHORT_).subtract('1','d');
		} else {
			console.warn("[Hotel Calendar] Invalid date format!");
			return;
		}
		this.updateView_();
	},
	
	advance: function(amount, step) {
		var $this = this;
		var cur_date = this.options.startDate.clone();
		this.options.startDate.add(amount, step);
		this.updateView_();
		this.e.dispatchEvent(new CustomEvent(
			'hcOnChangeDate',
			{'detail': {'prevDate':cur_date, 'newDate': $this.options.startDate}}));
	},
	
	back: function(amount, step) {
		var $this = this;
		var cur_date = this.options.startDate.clone();
		this.options.startDate.subtract(amount, step);
		this.updateView_();
		this.e.dispatchEvent(new CustomEvent(
			'hcOnChangeDate', 
			{'detail': {'prevDate':cur_date, 'newDate': $this.options.startDate}}));
	},
	
	//==== RESERVATIONS
	clearReservations: function() {
		var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
		for (var i=reservs.length; i>0; this.e.removeChild(reservs[--i]));
	},
	
	setReservations: function(reservations) {
		this.reservations = reservations || [];
		this.updateReservations_();
	},
	
	getReservationsByDay: function(day) {
		var $this = this;
		var day = this.toMoment(day);
		if (!day) {
			return false;
		}
		
		var reservs = []
		this.reservations.forEach(function(item, index){
			var start_date = moment(item.start_date, $this.DATE_FORMAT_SHORT_);
			var end_date = moment(item.end_date, $this.DATE_FORMAT_SHORT_);
			var diff_date = end_date.diff(start_date, 'days');
			
			for (var i=0; i<=diff_date; i++) {
				var ndate = start_date.clone().add(i,'d');
				if (ndate.format($this.DATE_FORMAT_SHORT_) === day.format($this.DATE_FORMAT_SHORT_)) {
					reservs.push(item);
				}
			}
		});
		
		return reservs;
	},
	
	//==== CELLS
	getCell: function(date, type, number, bednum) {
		var elms = this.etable.querySelectorAll("td[data-hcal-date='"+date+"'] table td[data-hcal-bed-num='"+bednum+"']");
		for (var i=0; i<elms.length; i++) {
			var parentRow = this.$base.querySelector('#'+elms[i].dataset.hcalParentRow);
			if (!parentRow || 
					parentRow.dataset.hcalRoomType != type || parentRow.dataset.hcalRoomNumber != number) {
				continue;
			}
			return elms[i];
		}
		
		return false;
	},
	
	getCells: function(cellInit, cellEnd) {
		var parentRow = this.$base.querySelector('#'+cellInit.dataset.hcalParentRow);
		var parentCell = this.$base.querySelector('#'+cellInit.dataset.hcalParentCell);
		if (!parentRow || !parentCell) {
			return [];
		}
		var start_date = moment(parentCell.dataset.hcalDate, this.DATE_FORMAT_SHORT_);
		parentCell = this.$base.querySelector('#'+cellEnd.dataset.hcalParentCell);
		var end_date = moment(parentCell.dataset.hcalDate, this.DATE_FORMAT_SHORT_);
		var diff_date = end_date.diff(start_date, 'days');
		
		var cells=[];
		for (var i=0; i<=diff_date; i++) {
			var cell = this.getCell(
				start_date.clone().add(i,'d').format(this.DATE_FORMAT_SHORT_),
				parentRow.dataset.hcalRoomType,
				parentRow.dataset.hcalRoomNumber,
				cellInit.dataset.hcalBedNum
			);
			cells.push(cell);
		}
		return cells;
	},
	
	//==== ROOMS
	getDayRoomTypeReservations: function(day, room_type) {
		var reservs = this.getReservationsByDay(day);
		var nreservs = [];
		reservs.forEach(function(item, index){
			if (item.room_type === room_type) {
				nreservs.push(item);
			}
		});
		return nreservs;
	},
	
	getRoomsByType: function(type) {
		var $this = this;
		rooms = [];
		var keys = Object.keys(this.options.rooms);
		keys.forEach(function(item, index){
			var room = $this.options.rooms[item];
			if (room.type === type)
				rooms.push(room);
		});
		return rooms;
	},
	
	getRoomTypes: function() {
		var $this = this;
		var room_types = [];
		var keys = Object.keys(this.options.rooms);
		keys.forEach(function(item, index){
			var room = $this.options.rooms[item];
			room_types.push(room.type);
		});
		
		return Array.from(new Set(room_types));
	},
	
	getRoom: function(number) {
		if (number in this.options.rooms)
			return this.options.rooms[number]
		return null;
	},
	
	//==== DETAIL CALCS
	calcDayRoomTypeReservations: function(day, room_type) {
		var day = this.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getDayRoomTypeReservations(day, room_type);
		var num_rooms = this.getRoomsByType(room_type).length;
		return Math.round(num_rooms-reservs.length);
	},
	
	calcReservationOccupation: function(day) {
		var day = this.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getReservationsByDay(day);
		return Math.round(reservs.length/this.numRooms*100.0);
	},
	
	
	/** PRIVATE MEMBERS **/
	//==== CONFIG
	DATE_FORMAT_SHORT_: "DD/MM/YYYY",
	
	//==== MAIN FUNCTIONS
	create_: function() {
		this.e.innerHTML = "";
		if (this.tableCreated) {
			console.warn("Hotel Calendar already created!");
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
		
		/** Main Events **/
		var $this = this;
		// TODO: In the future use 'ResizeObserver'
		window.addEventListener('resize', function(ev){
			$this.updateReservations_();
		});
	},
	
	generateTableDay_: function(parentCell) {
		var $this = this;
		var table = document.createElement("table");
		table.classList.add('hcal-table-day');
		table.classList.add('noselect');
		var row = false;
		var cell = false;
		var roomNumber = $this.$base.querySelector('#'+parentCell.dataset.hcalParentRow).dataset.hcalRoomNumber;
		var room = $this.getRoom(roomNumber);
		var num = (room.shared?room.persons:1);
		for (var i=0; i<num; i++) {
			row = table.insertRow();
			cell = row.insertCell();
			cell.dataset.hcalParentRow = parentCell.dataset.hcalParentRow;
			cell.dataset.hcalParentCell = parentCell.getAttribute('id');
			cell.dataset.hcalBedNum = i;
			cell.addEventListener('mouseenter', function(ev){
				if ($this.isLeftButtonPressed_(ev)) {
					if (!$this.cellSelection.start) {
						$this.cellSelection.start = this;
					} else if ($this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow &&
							$this.cellSelection.start.dataset.hcalBedNum === this.dataset.hcalBedNum) {
						$this.cellSelection.current = this;
					}
					$this.updateCellSelection_();
				}
			});
			cell.addEventListener('mousedown', function(ev){
				$this.cellSelection.start = $this.cellSelection.current = this;
				$this.cellSelection.end = false;
				$this.updateCellSelection_();
			});
			cell.addEventListener('mouseup', function(ev){
				if ($this.cellSelection.start && $this.cellSelection.start.dataset.hcalParentRow === this.dataset.hcalParentRow &&
						$this.cellSelection.start.dataset.hcalBedNum === this.dataset.hcalBedNum) {
					$this.cellSelection.end = this;
					$this.updateCellSelection_();
					
					$this.e.dispatchEvent(new CustomEvent(
						'hcalOnChangeSelection', 
						{'detail': {'cellStart':$this.cellSelection.start, 'cellEnd': $this.cellSelection.end}}));
				}
			});
		}
		
		return table;
	},
	
	get_normalized_rooms_: function() {
		var rooms = {};
		if (this.options.rooms) {
			var $this = this;
			var keys = Object.keys(this.options.rooms);
			
			keys.forEach(function(item, index){
				var room = $this.options.rooms[item];
				rooms[item] = [room.type.toAbbreviation(), room.persons];
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
			var str_date = this.options.startDate.format(this.DATE_FORMAT_SHORT_);
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
		var now = moment(new Date(), this.DATE_FORMAT_SHORT_);
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id',"hday_"+dd.format('DD_MM_YYYY'));
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format('DD-MM-YYYY');
			cell.textContent = dd.format("DD");
			cell.setAttribute('title', dd.format("dddd"))
			var day = +dd.format("D");
			if (day == 1) {
				cell.classList.add('hcal-cell-start-month');
				cur_month = dd.format("MMMM");
				months[cur_month] = {};
				months[cur_month].year = dd.format("YYYY");
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
		month_keys.forEach(function(item, index){
			var cell_month = row_init.insertCell();
			cell_month.setAttribute('colspan', months[item].colspan);
			cell_month.innerText = item + " "+months[item].year;
			cell_month.classList.add('hcal-cell-month');
			cell_month.classList.add('btn-hcal');
			cell_month.classList.add('btn-hcal-3d');
		});

		/** ROOM LINES **/
		var tbody = document.createElement("tbody");
		this.etable.appendChild(tbody);
		if (this.options.rooms) {
			var keys = Object.keys(this.options.rooms);
			keys.forEach(function(item, index){
				var room = $this.options.rooms[item];
				var room_type = room.type;
				// Room Number
				row = tbody.insertRow();
				row.setAttribute('id', "ROW_"+room_type+"_"+item+"_"+index);
				row.dataset.hcalRoomType = room_type;
				row.dataset.hcalRoomNumber = item;
				row.classList.add('hcal-row-room-type-group-item');
				cell = row.insertCell();
				cell.textContent = item;
				cell.classList.add('hcal-cell-room-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-3d');
				cell = row.insertCell();
				cell.textContent = room_type.toAbbreviation();
				cell.classList.add('hcal-cell-room-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', room_type+"_"+item+"_"+index+"_"+dd.format("DD_MM_YY"));
					cell.classList.add('hcal-cell-room-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
					// Generate Interactive Table
					cell.appendChild($this.generateTableDay_(cell));
					//cell.innerHTML = dd.format("DD");
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
	},
	
	create_table_detail_days_: function() {
		var $this = this;
		this.edtable.innerHTML = "";
		/** DETAIL DAYS HEADER **/
		var now = moment(new Date(), this.DATE_FORMAT_SHORT_);
		var thead = this.edtable.createTHead();
		var row = thead.insertRow();
		var cell = row.insertCell();
		cell.setAttribute('colspan', 2);
		cell.setAttribute('class', 'col-xs-1 col-lg-1');
		for (var i=0; i<this.options.days; i++) {
			var dd = this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id',"hday_"+dd.format('DD_MM_YYYY'));
			cell.classList.add('hcal-cell-header-day');
			cell.classList.add('btn-hcal');
			cell.classList.add('btn-hcal-3d');
			cell.dataset.hcalDate = dd.format('DD-MM-YYYY');
			cell.textContent = dd.format("DD");
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
			for (var item in room_types) {
				var room_type = room_types[item];
				row = tbody.insertRow();
				row.setAttribute('id', "ROW_DETAIL_FREE_TYPE_"+room_type);
				row.dataset.hcalRoomType = room_type;
				row.classList.add('hcal-row-detail-room-free-type-group-item');
				cell = row.insertCell();
				cell.textContent = room_type.toAbbreviation();
				cell.classList.add('hcal-cell-detail-room-free-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', room_type+"_"+item+"_"+dd.format("DD_MM_YY"));
					cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
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
		for (var i=0; i<$this.options.days; i++) {
			var dd = $this.options.startDate.clone().add(i,'d');
			cell = row.insertCell();
			cell.setAttribute('id', "CELL_DETAIL_TOTAL_FREE_"+dd.format("DD_MM_YY"));
			cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
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
			cell.setAttribute('id', "CELL_DETAIL_PERC_OCCUP_"+dd.format("DD_MM_YY"));
			cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
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
			for (var item in room_types) {
				var room_type = room_types[item];
				row = tbody.insertRow();
				row.setAttribute('id', "ROW_DETAIL_PRICE_TYPE_"+room_type);
				row.dataset.hcalRoomType = room_type;
				row.classList.add('hcal-row-detail-room-price-type-group-item');
				cell = row.insertCell();
				cell.textContent = room_type.toAbbreviation()+" €";
				cell.classList.add('hcal-cell-detail-room-price-type-group-item');
				cell.classList.add('btn-hcal');
				cell.classList.add('btn-hcal-flat');
				cell.setAttribute("colspan", "2");
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.setAttribute('id', room_type+"_"+item+"_"+dd.format("DD_MM_YY"));
					cell.classList.add('hcal-cell-detail-room-price-type-group-item-day');
					cell.dataset.hcalParentRow = row.getAttribute('id');
					cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
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
			}
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
			cell.setAttribute('id', "CELL_DETAIL_MIN_STAY_"+dd.format("DD_MM_YY"));
			cell.classList.add('hcal-cell-detail-room-min-stay-group-item-day');
			cell.dataset.hcalParentRow = row.getAttribute('id');
			cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
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
		var cellStart = this.cellSelection.start;
		var cellEnd = (this.cellSelection.end?this.cellSelection.end:this.cellSelection.current)
		if (cellStart && cellEnd) {
			var cells = this.getCells(cellStart, cellEnd);
			cells.forEach(function(item, index){
				item.classList.add('hcal-cell-highlight');
			});
		}
	},
	
	updateReservations_: function() {
		var $this = this;
		this.clearReservations();
		
		this.reservations.forEach(function(item, index){
			for (var indexb=0; indexb<item.persons; indexb++) {
				var start_date = moment(item.start_date, $this.DATE_FORMAT_SHORT_);
				var end_date = moment(item.end_date, $this.DATE_FORMAT_SHORT_);
				var diff_date = end_date.diff(start_date, 'days');
				
				// Search start cell
				var cellInit = $this.getCell(item.start_date, item.room_type, item.room_number, indexb);
				if (!cellInit) {
					for (var i=0; i<=diff_date; i++) {
						cellInit = $this.getCell(
							start_date.clone().add(i,'d').format($this.DATE_FORMAT_SHORT_), 
							item.room_type, 
							item.room_number, 
							indexb);
						if (cellInit) {
							cellInit.dataset.hcalReservationCellType = 'soft-start';
							break;
						}
					}
				} else {
					cellInit.dataset.hcalReservationCellType = 'hard-start';
				}
				// Search end cell
				var cellEnd = $this.getCell(item.end_date, item.room_type, item.room_number, indexb);
				if (!cellEnd) {
					for (var i=0; i<=diff_date; i++) {
						cellEnd = $this.getCell(
							end_date.clone().subtract(i,'d').format($this.DATE_FORMAT_SHORT_), 
							item.room_type, 
							item.room_number, 
							indexb);
						if (cellEnd) {
							cellEnd.dataset.hcalReservationCellType = 'soft-end';
							break;
						}
					}
				} else {
					cellEnd.dataset.hcalReservationCellType = 'hard-end';
				}
				
				// Fill
				if (cellInit && cellEnd) {
					var etableOffset = $($this.etable).offset();
					
					var divRes = document.createElement('div');
					divRes.dataset.hcalReservationId = index;
					divRes.classList.add('hcal-reservation');
					divRes.classList.add('noselect');
					divRes.innerText = item.title;
					var boundsInit = cellInit.getBoundingClientRect();
					var boundsEnd = cellEnd.getBoundingClientRect();
					divRes.style.top=(boundsInit.top-etableOffset.top)+'px';
					divRes.style.height=(boundsInit.height)+'px';
					divRes.style.lineHeight=(boundsInit.height-2)+'px'
					if (cellInit.dataset.hcalReservationCellType === 'soft-start') {
						divRes.style.borderLeftWidth = "0";
						divRes.style.borderTopLeftRadius = "0";
						divRes.style.borderBottomLeftRadius = "0";
						divRes.style.left=(boundsInit.left-etableOffset.left)+'px';
						divRes.style.width=(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0+'px';
					} else if (cellEnd.dataset.hcalReservationCellType !== 'soft-end') {
						divRes.style.left=(boundsInit.left-etableOffset.left)+boundsInit.width/2.0+'px';
					}
					if (cellEnd.dataset.hcalReservationCellType === 'soft-end') {
						divRes.style.borderRightWidth = "0";
						divRes.style.borderTopRightRadius = "0";
						divRes.style.borderBottomRightRadius = "0";
						divRes.style.left=(boundsInit.left-etableOffset.left)+boundsInit.width/2.0+'px';
						divRes.style.width=(boundsEnd.left-boundsInit.left)+boundsEnd.width/2.0+'px';
					} else if (cellInit.dataset.hcalReservationCellType !== 'soft-start') {
						divRes.style.width=(boundsEnd.left-boundsInit.left)+'px';
					}
					$this.e.appendChild(divRes);
					
					var cells = $this.getCells(cellInit, cellEnd);
					cells.forEach(function(itemc, indexc){
						itemc.classList.add('hcal-cell-room-type-group-item-day-occupied');
						itemc.dataset.hcalReservationId = index;
					});
				}
			}
		});
		
		this.assignReservationsEvents_();
	},
	
	assignReservationsEvents_: function() {
		var $this = this;
		var reservs = this.e.querySelectorAll('div.hcal-reservation');
		reservs.forEach(function(item, index) {
			var bounds = item.getBoundingClientRect();
			item.addEventListener('mousemove', function(ev){
				var posAction = $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY);
				if (posAction == 'r') { // Right
					item.style.cursor = "col-resize";
				} else if (posAction == 'l') { // Left
					item.style.cursor = "col-resize";
				} else {
					item.style.cursor = "pointer";
				}
			});
			item.addEventListener('mousedown', function(ev){
				if (!$this.reservationActived) {
					$this.reservationActived = this;
					this.classList.add('hcal-reservation-action');
					var posAction = $this.getRerservationPositionAction_(this, ev.layerX, ev.layerY);
				}
			});
		});
	},
	
	getRerservationPositionAction_: function(elm, posX, posY) {
		var bounds = elm.getBoundingClientRect();
		if (posX <= 5) { return 'r'; }
		else if (posX >= bounds.width-10) { return 'l' }
		return 'c';
	},
	
	updateReservationOccupation_: function() {
		var cells = this.etable.querySelectorAll('td.hcal-cell-month-day-occupied');
		for (var i=0; i<cells.length; i++) {
			var parentCell = this.$base.querySelector('#'+cells[i].dataset.hcalParentCell);
			var cell_date = parentCell.dataset.hcalDate;
			var perOccup = this.calcReservationOccupation(cell_date);
			cells[i].innerText = perOccup+'%';
			cells[i].style.backgroundColor = this.generateColor_(perOccup, 100, 0.35, false, true);
		}
	},
	
	//==== HELPER FUNCTIONS
	sameSimpleDate_: function(dateA, dateB) {
		return dateA.isSame(dateB,'day') && dateA.isSame(dateB,'month') && dateA.isSame(dateB,'year');
	},
	
	isLeftButtonPressed_: function(evt) {
	    evt = evt || window.event;
	    if ("buttons" in evt) {
	        return evt.buttons == 1;
	    }
	    var button = evt.which || evt.button;
	    return button == 1;
	},
	
	toMoment: function(date) { 
		if (moment.isMoment(date)) {
			return date;
		} else if (typeof date === 'string') {
			date = moment(date, this.DATE_FORMAT_SHORT_);
			if (moment.isMoment(date)) {
				return date;
			}
		}
		console.warn('[Hotel Calendar][toMoment] Invalid date format!');
		return false;
	},
	
	//==== EVENT FUNCTIONS
	onMainMouseUp: function(ev) {
		if (this.reservationActived) {
			this.reservationActived.classList.remove('hcal-reservation-action');
			this.reservationActived = false;
		}
	},
	
	onClickSelectorDate: function(ev, elm) {
		var $this = this;
		function setSelectorDate(elm) {
			var new_date = moment(elm.value, $this.DATE_FORMAT_SHORT_);
			var span = document.createElement('span');
			span.addEventListener('click', function(ev){ $this.onClickSelectorDate(ev, elm); });
			if (new_date.isValid()) {
				$this.setStartDate(new_date);
			} else {
				$this.setStartDate(moment(new Date()));
			}
		}
		var str_date = this.options.startDate.format(this.DATE_FORMAT_SHORT_);
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
	hueToRgb_: function(v1, v2, h) {
		if (h<0.0) { h+=1; }
		if (h>1.0) { h-=1; }
		if ((6.0*h) < 1.0) { return v1+(v2-v1)*6.0*h; }
		if ((2.0*h) < 1.0) { return v2; }
		if ((3.0*h) < 2.0) { return v1+(v2-v1)*((2.0/3.0)-h)*6.0; }
		return v1;
	},
	
	hslToRgb_: function(h,s,l) {
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
	
	generateColor_: function(value, max, offset, reverse, strmode) {
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
}

odoo.define('alda_calendar.HotelCalendarJS', function (require) {
"use strict";
/*
 * Hotel Calendar JS v0.0.1a
 * GNU Public License - 2017
 * Aloxa Solucions S.L. <info@aloxa.eu>
 * Alexandre Díaz <alex@aloxa.eu>
 */

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
			Created: "27/01/2017",
			Updated: ""
		};
	}
	
	this.e.style.overflowY = "scroll";
	/** Options **/
	if (!options) { options = {}; }
	this.options = {
		startDate: moment(options.startDate || new Date(), this.DATE_FORMAT_SHORT_),
		days: options.days || 15,
		rooms: options.rooms || {},
	};
	
	/** Internal Values **/
	this.reservations = reservations;
	this.tableCreated = false;
	this.cellSelection = {start:false, end:false, current:false};
	var $this = this;
	this.numRooms = 0;
	var keys = Object.keys(this.options.rooms);
	keys.forEach(function(item, index){
		$this.numRooms += $this.options.rooms[item].numbers.length;
	});
	
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
	
	update: function(data) {
		this.data = data;
		this.updateView_();
	},
	
	setSelectorDate(date) {
		if (moment.isMoment(date)) {
			this.options.startDate = date;
		} else if (typeof date === 'string'){
			this.options.startDate = moment(date, this.DATE_FORMAT_SHORT_);
		} else {
			console.warn("[Hotel Calendar] Invalid date format!");
			return;
		}
		this.updateView_();
	},
	
	hideRoomType: function(type) {
		var show = false;
		var num_rows = this.etable.rows.length;
		var parent_group = false;
		for (var i=0; i<num_rows; i++) {
			var row = this.etable.rows[i];
			if (row.dataset.hcalRoomType === type) {
				if (row.style.display !== "none") {
					row.style.display = "none";
					show = false;
				} else {
					row.style.display = "table-row";
					show = true;
				} 
			}
			if ('roomTypeGroup' in row.dataset && row.dataset.hcalRoomTypeGroup === type) {
				parent_group = row;
			}
		}
		
		if (parent_group) {
			parent_group.cells[0].innerHTML = (show?"&uarr; ":"&darr; ")+type;
		}
		this.updateReservations_();
	},
	
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
	
	clearTable: function() {
		/** Reset Reservations **/
		var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
		for (var i=0; i<reservs.length; i++) {
			this.e.removeChild(reservs[i]);
		}
	},
	
	getDayRoomTypeReservations: function(day, room_type) {
		var reservs = this.getDayReservations(day);
		var nreservs = [];
		reservs.forEach(function(item, index){
			if (item.room_type === room_type) {
				nreservs.push(item);
			}
		});
		return nreservs;
	},
	
	calcDayRoomTypeReservations: function(day, room_type) {
		var day = this.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getDayRoomTypeReservations(day, room_type);
		var num_rooms = this.options.rooms[room_type].numbers.length;
		return Math.round(num_rooms-reservs.length);
	},
	
	getDayReservations: function(day) {
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
	
	calcReservationOccupation: function(day) {
		var day = this.toMoment(day);
		if (!day) {
			return false;
		}

		var reservs = this.getDayReservations(day);
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
		this.e.appendChild(this.etable);
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
		var num = $this.$base.querySelector('#'+parentCell.dataset.hcalParentRow).dataset.hcalRoomPersons;
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
	
	//==== UPDATE FUNCTIONS
	updateView_: function() {
		var $this = this;
		/** Reset Table **/
		for (var i=0; i<this.etable.rows.length; i++) {
			this.etable.deleteRow(i);
		}
		this.etable.deleteTHead();
		/** Table Header **/
		var thead = this.etable.createTHead();
		var row = thead.insertRow();
		var row_init = row;
		// Current Date
		var cell = row.insertCell();
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
			var cur_date = $this.options.startDate.clone();
			$this.options.startDate.subtract('1', 'd');
			$this.updateView_();
			ev.preventDefault();
			$this.e.dispatchEvent(new CustomEvent(
				'hcOnChangeDate',
				{'detail': {'prevDate':cur_date, 'newDate': $this.options.startDate}}));
		});
		cell.insertBefore(link, cell.firstChild);
		// Button Next Day
		link = document.createElement("a");
		link.setAttribute('href', '#');
		link.innerHTML = "&raquo";
		link.addEventListener('click', function(ev){
			var cur_date = $this.options.startDate.clone();
			$this.options.startDate.add('1', 'd');
			$this.updateView_();
			ev.preventDefault();
			$this.e.dispatchEvent(new CustomEvent(
				'hcOnChangeDate', 
				{'detail': {'prevDate':cur_date, 'newDate': $this.options.startDate}}));
		});
		cell.appendChild(link);
		cell.setAttribute('rowspan', 2);
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
			cell.dataset.hcalDate = dd.format('DD-MM-YYYY');
			var tableDay = document.createElement('table');
			tableDay.classList.add('hcal-table-header-day');
			var cellDay = tableDay.insertRow().insertCell();
			cellDay.innerText = '0%';
			cellDay.dataset.hcalParentCell = cell.getAttribute('id');
			cellDay.style.backgroundColor = "green"; // TODO
			cellDay.classList.add('hcal-cell-month-day-occupied');
			cellDay = tableDay.insertRow().insertCell();
			cellDay.innerHTML = dd.format("dd")+"<br/>"+dd.format("D");
			cellDay.classList.add('hcal-cell-month-day');
			cell.appendChild(tableDay);
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
			}
			++months[cur_month].colspan;
		}
		// Render Months
		var month_keys = Object.keys(months);
		month_keys.forEach(function(item, index){
			var cell_month = row_init.insertCell();
			cell_month.setAttribute('colspan', months[item].colspan);
			cell_month.innerText = item + " ("+months[item].year+")";
			cell_month.classList.add('hcal-cell-month');
		});
		
		/** Table Rooms **/
		if (this.options.rooms) {
			var $this = this;
			var keys = Object.keys(this.options.rooms);
			keys.forEach(function(item, index){
				// Room Type Group
				var room_type = item;
				row = $this.etable.insertRow();
				row.dataset.hcalRoomTypeGroup = room_type;
				row.classList.add('hcal-row-room-type-group');
				cell = row.insertCell();
				cell.innerHTML = "&uarr; "+room_type;
				cell.classList.add('hcal-cell-room-type');
				cell.addEventListener('click', function(){
					$this.hideRoomType(room_type);
				});
				for (var i=0; i<$this.options.days; i++) {
					var dd = $this.options.startDate.clone().add(i,'d');
					cell = row.insertCell();
					cell.classList.add('hcal-cell-room-type-group-day');
					cell.dataset.hcalDate = dd.format($this.DATE_FORMAT_SHORT_);
					cell.dataset.hcalRoomType = room_type;
					cell.setAttribute('id', 'room-group_'+room_type+'_'+dd.format("DD_MM_YY"));
					var tableGroupDay = document.createElement('table');
					tableGroupDay.classList.add('hcal-table-type-group-day');
					var cellGroupDay = tableGroupDay.insertRow().insertCell();
					cellGroupDay.dataset.hcalParentCell = cell.getAttribute('id');
					cellGroupDay.classList.add('hcal-cell-type-group-day-free');
					cellGroupDay.style.backgroundColor = "red"; // TODO
					cellGroupDay.innerText="0";
					cellGroupDay = tableGroupDay.insertRow().insertCell();
					cellGroupDay.classList.add('hcal-cell-type-group-day-price');
					cellGroupDay.innerText="0.00€";
					cell.appendChild(tableGroupDay);
					var day = +dd.format("D");
					if (day == 1) {
						cell.classList.add('hcal-cell-start-month');
					}
					if ($this.sameSimpleDate_(dd, now)) {
						cell.classList.add('hcal-cell-current-day');
					}
				}
				// Room Number
				$this.options.rooms[item].numbers.forEach(function(itemb, indexb) {
					row = $this.etable.insertRow();
					row.setAttribute('id', item+"_"+itemb+"_"+indexb)
					row.dataset.hcalRoomType = room_type;
					row.dataset.hcalRoomNumber = itemb;
					row.dataset.hcalRoomPersons = $this.options.rooms[item].persons;
					row.classList.add('hcal-row-room-type-group-item');
					cell = row.insertCell();
					cell.innerHTML = itemb;
					cell.classList.add('hcal-cell-room-type-group-item');
					for (var i=0; i<$this.options.days; i++) {
						var dd = $this.options.startDate.clone().add(i,'d');
						cell = row.insertCell();
						cell.setAttribute('id', item+"_"+itemb+"_"+indexb+"_"+dd.format("DD_MM_YY"));
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
						}
					}
				});
			});
		}
		
		this.updateReservations_();
		this.updateReservationOccupation_();
		this.updateRoomTypeFreeRooms_();
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
		/** Reset Reservations **/
		var reservs = this.e.querySelectorAll('.hcal-reservation') || [];
		for (var i=0; i<reservs.length; i++) {
			this.e.removeChild(reservs[i]);
		}
		this.reservations.forEach(function(item, index){
			item.room_beds.forEach(function(itemb, indexb){
				var start_date = moment(item.start_date, $this.DATE_FORMAT_SHORT_);
				var end_date = moment(item.end_date, $this.DATE_FORMAT_SHORT_);
				var diff_date = end_date.diff(start_date, 'days');
				
				// Search start cell
				var cellInit = $this.getCell(item.start_date, item.room_type, item.room_number, itemb);
				if (!cellInit) {
					for (var i=0; i<=diff_date; i++) {
						cellInit = $this.getCell(
							start_date.clone().add(i,'d').format($this.DATE_FORMAT_SHORT_), 
							item.room_type, 
							item.room_number, 
							itemb);
						if (cellInit) {
							cellInit.dataset.hcalReservationCellType = 'soft-start';
							break;
						}
					}
				} else {
					cellInit.dataset.hcalReservationCellType = 'hard-start';
				}
				// Search end cell
				var cellEnd = $this.getCell(item.end_date, item.room_type, item.room_number, itemb);
				if (!cellEnd) {
					for (var i=0; i<=diff_date; i++) {
						cellEnd = $this.getCell(
							end_date.clone().subtract(i,'d').format($this.DATE_FORMAT_SHORT_), 
							item.room_type, 
							item.room_number, 
							itemb);
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
					divRes.innerText = item.title;
					var boundsInit = cellInit.getBoundingClientRect();
					var boundsEnd = cellEnd.getBoundingClientRect();
					divRes.style.left=(boundsInit.left-etableOffset.left)+4+'px';
					divRes.style.top=(boundsInit.top-etableOffset.top)+'px';
					divRes.style.width=((boundsEnd.left+boundsEnd.width)-boundsInit.left)-12+'px';
					divRes.style.height=(boundsInit.height)+'px';
					if (cellInit.dataset.hcalReservationCellType === 'soft-start') {
						divRes.style.borderLeftWidth = "0";
					}
					if (cellEnd.dataset.hcalReservationCellType === 'soft-end') {
						divRes.style.borderRightWidth = "0";
					}
					$this.e.appendChild(divRes);
					
					var cells = $this.getCells(cellInit, cellEnd);
					cells.forEach(function(itemc, indexc){
						itemc.classList.add('hcal-cell-room-type-group-item-day-occupied');
						itemc.dataset.hcalReservationId = index;
					});
				}
			});
		});
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
	
	updateRoomTypeFreeRooms_: function(){
		var cells = this.etable.querySelectorAll('td.hcal-cell-type-group-day-free');
		for (var i=0; i<cells.length; i++) {
			var parentCell = this.$base.querySelector('#'+cells[i].dataset.hcalParentCell);
			var cell_date = parentCell.dataset.hcalDate;
			var room_type = parentCell.dataset.hcalRoomType;
			var num = this.calcDayRoomTypeReservations(cell_date, room_type);
			cells[i].innerText = num;
			var num_rooms = this.options.rooms[room_type].numbers.length;
			cells[i].style.backgroundColor = this.generateColor_(num, num_rooms, 0.35, true, true);
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
	onClickSelectorDate: function(ev, elm) {
		var $this = this;
		function setSelectorDate(elm) {
			var new_date = moment(elm.value, $this.DATE_FORMAT_SHORT_);
			var span = document.createElement('span');
			span.addEventListener('click', function(ev){ $this.onClickSelectorDate(ev, elm); });
			if (new_date.isValid()) {
				$this.setSelectorDate(new_date);
			} else {
				$this.setSelectorDate(moment(new Date()));
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
		var rgb = [1.0*offset,1.0,0.5];
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

	return HotelCalendar;
});

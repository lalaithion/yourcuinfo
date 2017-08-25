$(document).ready(function() {
  state = {
    expandedRows: {},
    selectedSections: [],
    searchTerms: {
      // Bit flag meaning enable all days
      days: 31,
    },
  };

  function unpackData(rowData) {
    return {
      code: rowData[0],
      title: rowData[1],
      units: rowData[2],
      currentStatus: rowData[3],
      description: rowData[4],
      openSeats: rowData[5],
      waitlist: rowData[6],
      sections: rowData.slice(7),
    };
  }

  function zeroPad(n, width) {
    n = n.toString();
    return n.length < width ? new Array(width - n.length + 1).join('0') + n : n;
  }

  // Days are bitmasks for ease of transmitting and comparison.
  function dayToString(dayBitmask) {
    days = { 1: 'Mo', 2: 'Tu', 4: 'We', 8: 'Th', 16: 'Fr'};
    dayString = '';
    for(i in days) {
      if(dayBitmask & i) {
        dayString += days[i];
      }
    }
    return dayString;
  }

  function timeToString(time) {
    hour = Math.floor(time / 60);
    minute = time % 60;
    suffix = 'AM';
    if(hour > 12) {
      hour = hour - 12;
      suffix = 'PM';
    }
    return hour + ':' + zeroPad(minute,2) + suffix;
  }

  var filterList = {
    full: {
      parentRow: function(settings, data, dataIndex) {
        return data[3] == "open";
      },
      child: function(id, data) {
        return data[3] > 0;
      },
      active: false
    },
    description: {
      parentRow: function(settings, data, dataIndex) {
        searchTerm = state.searchTerms.description;
        return data[1].search(searchTerm) >= 0 ||
               data[4].search(searchTerm) >= 0;
      },
      child: function() {
        return true;
      },
      active: false
    },
    instructor: {
      // TODO(Alex) figure out why data is only the first 5 indices.
      parentRow: function(settings, data, dataIndex) {
        data = table.row(dataIndex).data()
        for(section of data.slice(7)) {
          if(section[6].search(state.searchTerms.instructor) >= 0) {
            return true;
          }
        }
        return false;
      },
      child: function(childName, data) {
        return data[6].search(state.searchTerms.instructor) >= 0;
      },
      active: false
    },
    selected: {
      parentRow: function(settings, data, dataIndex) {
        for(id of state.selectedSections) {
          if(id.substring(0,9) == data[0]) {
            return true;
          }
        }
        return false;
      },
      child: function(childName, data) {
        for(id of state.selectedSections) {
          if(id == childName) {
            return true;
          }
        }
        return false;
      },
      active: false
    },
    conflicting: {
      parentRow: function(settings, data, dataIndex) {
        data = table.row(dataIndex).data()
        sections = unpackData(data).sections;
        for(id of state.selectedSections) {
          for(section of sections) {
            if(section[1] == "TBA") {
              return true;
            }
            selectedTime = state.selectedSections[id].classTime;
            rowTime = formatDays(section[1]);
            for(rowDay of rowTime.days) {
              for(selectedDay of selectedTime.days) {
                if(rowDay != selectedDay ||
                   (timeIsBefore(rowTime.end, selectedTime.start) ||
                   timeIsBefore(selectedTime.end, rowTime.start))) {
                   return true;
                }
              }
            }
          }
        }
        return false;
      },
      child: function(rowID, data) {
        for(id of state.selectedSections) {
          if(id == rowID) {
            return true;
          }
          selectedTime = state.selectedSections[id].classTime;
          rowTime = formatDays(data[1]);
          for(rowDay of rowTime.days) {
            for(selectedDay of selectedTime.days) {
              if(rowDay == selectedDay &&
                 !(timeIsBefore(rowTime.end, selectedTime.start) ||
                 timeIsBefore(selectedTime.end, rowTime.start))) {
                 return false;
              }
            }
          }
        }
        return true;
      },
      active: false
    },
    days: {
      parentRow: function(settings, data, dataIndex) {
        data = table.row(dataIndex).data()
        sections = unpackData(data).sections;
        for(section of sections) {
          if(section[1] == "TBA") {
            return true;
          }
          else {
            var disabledDays = ~state.searchTerms.days;
            if(!(section[1] & disabledDays)) {
              return true;
            }
          }
        }
        return false;
      },
      child: function(rowID, data) {
        var disabledDays = ~state.searchTerms.days & 0x1F;
        return !(data[1] & disabledDays);
      },
      active: true
    },
  };

  var childTemplate = document.getElementById('child-template');
  var sectionTemplate = document.getElementById('section-template');
  function createChild(parent_row) {
    var data = unpackData(table.row(parent_row).data())
    var newChild = childTemplate.cloneNode(true); // true for deep clone
    var newChildTable = newChild.querySelector("tbody");
    newChild.insertBefore(document.createTextNode(data.description),
         newChild.firstChild);
    newChild.style.display = null;

    state.expandedRows[data.code] = { parentRow: parent_row };
    data.sections.forEach(function(section, i) {
      var id = data.code + '-' + i;
      state.expandedRows[data.code][id] = section;
      for(filterName in filterList) {
        filter = filterList[filterName];
        if(filter.active && !filter.child(id, section)) {
          return;
        }
      }
      sectionRow = newChildTable.querySelector("tr").cloneNode(true);
      sectionRow.style.display = null;
      sectionRow.id = id;
      sectionRow.children[0].innerHTML = section[0];
      date = dayToString(section[1]) + ' ' + timeToString(section[2]) + '  - ' + timeToString(section[3])
      sectionRow.children[1].innerHTML = date;
      sectionRow.children[2].innerHTML = section[4];
      sectionRow.children[3].innerHTML = section[5];
      sectionRow.children[4].innerHTML = section[6];
      sectionRow.children[5].innerHTML = section[7];
      newChildTable.append(sectionRow);

      // Child was selected earlier - restore state
      if(state.selectedSections.indexOf(sectionRow.id) >= 0) {
        sectionRow.querySelector("input").checked = true;
        sectionRow.className += " selected";
      }
    });
    return newChild;
  }

  /*
   * Turns a myCUinfo-style date/time ("TuTh 2:00-2:50") into a 
   * fullCalendar-style date/time ("2014-06-09T14:50").
   * If you have to dig through it I am very sorry.
   *
   * Parameters:
   *   classDays (string): myCUinfo-style date/time ("TuTh 2:00-2:50" or similar)
   */
  function formatDays(classDays) {
    days = [ { day: "Mo", date: "09" }, { day: "Tu", date: "10" }, { day: "We", date: "11" }, { day: "Th", date: "12" }, { day: "Fr", date: "13" } ];
    var dates = days.reduce(function(acc, val) {
      return (classDays.indexOf(val.day) == -1) ? acc : acc.concat(`2014-06-${val.date}`);
    }, []);
    times = classDays.match(/(\d{1,2}):(\d{2})(.M) - (\d{1,2}):(\d{2})(.M)/);
    startHour = String(Number(times[1]) + ((times[3] == "PM" && times[1] != "12") ? 12 : 0));
    endHour = String(Number(times[4]) + ((times[6] == "PM" && times[4] != "12") ? 12 : 0));
    start = `${(startHour.length > 1)?'':'0'}${startHour}:${times[2]}`;
    end = `${(endHour.length > 1)?'':'0'}${endHour}:${times[5]}`;
    return {days: dates, start: start, end: end};
  }

  // Helper function to color-code calendar entries.
  function getColor(type) {
    switch(type) {
      case "lecture":
          return "#774444";
      case "recitation":
          return "#447744";
      default:
          return "grey";
    }
  }

  // https://www.w3schools.com/js/js_cookies.asp
  function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
  }

  function getCookie(cname) {
      var name = cname + "=";
      var decodedCookie = decodeURIComponent(document.cookie);
      var ca = decodedCookie.split(';');
      for(var i = 0; i <ca.length; i++) {
          var c = ca[i];
          while (c.charAt(0) == ' ') {
              c = c.substring(1);
          }
          if (c.indexOf(name) == 0) {
              return c.substring(name.length, c.length);
          }
      }
      return "";
  }

  // Instantiate table.
  var scrollPos = 0;
  var table = $('#table').DataTable({
    ajax: "docs/class_data.json",
    processing: true,
    scrollY: "500px",
    scrollCollapse: true,
    paging: false,
    deferRender: true,
    processing: true,
    sDom: 't',
    columns: [
      null,
      null,
      null,
      null,
      { "visible": false }
    ],
    // Used to avoid annoying scrolling bug
    preDrawCallback: function (settings) {
      scrollPos = $('.dataTables_scrollBody')[0].scrollTop;
    },
    drawCallback: function (settings) {
      $('.dataTables_scrollBody')[0].scrollTop = scrollPos;
    },
  });

  // Instantiate calendar.
  $('#calendar').fullCalendar({
    header: {
      left: '',
      center: '',
      right: '',
    },
    columnFormat: 'ddd',
    hiddenDays: [0, 6],
    defaultDate: '2014-06-12',
    defaultView: 'agendaWeek',
    minTime: '08:00:00',
    maxTime: '20:00:00',
    height: "auto",
    allDaySlot: false,
    editable: false,
    events: [],
    eventClick: function(calEvent, jsEvent, view) {
      console.log(state.expandedRows)
      offset = state.expandedRows[calEvent.id.substring(0,9)].parentRow.offsetTop;
      $('.dataTables_scrollBody').animate({ scrollTop: offset }, 500);
    },
  });

  // Used to store which courses have been selected and added to the calendar.
  // state.selectedSections = JSON.parse(getCookie("selected") || "[]");
  // TODO(alex) redo to work with new selectedSections format
  /*
  for(id in state.selectedSections) {
    data = state.selectedSections[id];
    createCalendarEvents(data.days, data.start, data.end, data.color, id);
  }
  */

  // fullCalendar-style date/time ("2014-06-09T14:50").
  function createCalendarEvents(days, start, end, color, id) {
    bitDays = {
      1: '09',
      2: '10',
      4: '11',
      8: '12',
      16: '13',
    };
    for(bit in bitDays) {
      if(bit & days) {
        dayString = '2014-06-' + bitDays[bit];
        startString = zeroPad(Math.floor(start / 60), 2) + ':' + zeroPad(start % 60, 2)
        endString = zeroPad(Math.floor(end / 60), 2) + ':' + zeroPad(end % 60, 2)
	var newEvent = {
	  title: id.substr(0,9),
	  start: dayString + 'T' + startString,
	  end: dayString + 'T' + endString,
	  color: color,
	  id: id,
	}
	$('#calendar').fullCalendar('renderEvent', newEvent, true)
      }
    };
  }

  function toggleSelected(dom_row) {
    child_row = $(dom_row);
    id = child_row.attr('id');
    data = state.expandedRows[id.substr(0,9)][id];
    // Delete any existing events
    $('#calendar').fullCalendar('removeEvents', id);
    sectionIndex = state.selectedSections.indexOf(id);
    if(sectionIndex < 0) {
      color = getColor(child_row.children()[0].innerHTML)
      state.selectedSections.push(id);
      createCalendarEvents(data[1], data[2], data[3], color, id);
    } else {
      state.selectedSections.splice(sectionIndex, 1);
    }
    setCookie("selected", JSON.stringify(state.selectedSections), 365);
    child_row.toggleClass('selected');
    dom_row.querySelector('input').checked = sectionIndex >= 0;
  }

  function toggleDetailedDescription(parent_row) {
    row = $(parent_row);
    row.toggleClass('shown');
    var row_handle = table.row(row);
    if (row_handle.child.isShown()) {
      delete state.expandedRows[row_handle.data()[0]];
      row_handle.child.hide();
    }
    else {
      row_handle.child(createChild(parent_row), 'child-body').show();
      // TODO(Alex): There should be a better way to do this that
      // also fixes hovering over the table header without a color change.
      /*row_handle.child().hover(function(){
        $(this).css("background-color", "white");
      });*/
    }
  }

  /* TODO(alex) Upgrade to work with new date format.
  $('#table tbody').on('mouseenter', 'tr', function(row) {
    row = $(row.currentTarget);
    if(row.hasClass("child-row")) {
      id = row.attr('id');
      dt = formatDays(row.children()[1].innerHTML);
      if(!state.selectedSections[id]) {
        createCalendarEvents(dt, '#AAA', id);
      }
    }
  });

  $('#table tbody').on('mouseleave', 'tr', function(row) {
    row = $(row.currentTarget);
      id = row.attr('id');
      if(!state.selectedSections[id]) {
        $('#calendar').fullCalendar('removeEvents', id);
      }
    }
  });*/

  // Callback when parent row is opened or child row is selected.
  $('#table tbody').on('click', 'tr', function (e) {
    var row = $(this);
    if(row.hasClass("child-body")) {
      return;
    }
    else if(row.hasClass("child-row")) {
      // TODO(alex) Upgrade to work with new date format.
      toggleSelected(this);
    }
    else {
      toggleDetailedDescription(this);
    }
  });

  $('#code-search').on('keyup change', function () {
    col = table.columns(0);
    if (col.search() !== this.value) {
      col.search(this.value).draw();
    }
  });

  $('#name-search').on('keyup change', function () {
    state.searchTerms.description = new RegExp(this.value, 'i');
    filterList.description.active = this.value != '';
    createFilters();
  });

  $('#instructor-search').on('keyup change', function () {
    state.searchTerms.instructor = new RegExp(this.value, 'i');
    filterList.instructor.active = this.value != '';
    createFilters();
  });

  function refreshTable() {
    for(id in state.expandedRows) {
      row = state.expandedRows[id].parentRow;
      table.row(row).child(createChild(row));
    }
    table.draw();
  }

  function createFilters() {
    $.fn.dataTable.ext.search = [];
    for (entry in filterList) {
      if (filterList[entry].active) {
        $.fn.dataTable.ext.search.push(filterList[entry].parentRow)
      }
    }
    refreshTable();
  }
  createFilters();

  $('#display-full').change(function(target) {
    filterList["full"].active = target.currentTarget.checked;
    createFilters();
  });

  $('#display-selected').change(function(target) {
    filterList["selected"].active = target.currentTarget.checked;
    createFilters();
  });

  $('#display-conflicting').change(function(target) {
    filterList["conflicting"].active = target.currentTarget.checked;
    createFilters();
  });

  days = ['#mon', '#tue', '#wed', '#thu', '#fri'];
  for(i in days) {
    (function(i) {
      $(days[i])[0].checked = true;
      $(days[i]).change(function(target) {
        mask = 1 << i;
        state.searchTerms.days ^= mask;
        refreshTable();
      });
    })(i);
  }
});

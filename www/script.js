$(document).ready(function() {
  expandedRows = {};
  selectedSections = {};
  searchTerms = {};

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

  function timeIsBefore(x, y) {
    xsplit = x.split(":");
    ysplit = y.split(":");
    return (xsplit[0] < ysplit[0]) || 
           ((xsplit[0] == ysplit[0]) && (xsplit[1] <= ysplit[1]))
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
        searchTerm = searchTerms.description;
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
          if(section[4].search(searchTerms.instructor) >= 0) {
            return true;
          }
        }
        return false;
      },
      child: function(childName, data) {
        return data[4].search(searchTerms.instructor) >= 0;
      },
      active: false
    },
    selected: {
      parentRow: function(settings, data, dataIndex) {
        for (id in selectedSections) {
          if(id.substring(0,9) == data[0]) {
            return true;
          }
        }
        return false;
      },
      child: function(childName, data) {
        for(id in selectedSections) {
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
        for(id in selectedSections) {
          for(section of sections) {
            if(section[1] == "TBA") {
              return true;
            }
            selectedTime = selectedSections[id].classTime;
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
        for(id in selectedSections) {
          if(id == rowID) {
            return true;
          }
          selectedTime = selectedSections[id].classTime;
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
    data.sections.forEach(function(section, i) {
      var id = data.code + '-' + i;
      for(filterName in filterList) {
        filter = filterList[filterName];
        if(filter.active && !filter.child(id, section)) {
          return;
        }
      }
      sectionRow = newChildTable.querySelector("tr").cloneNode(true);
      sectionRow.style.display = null;
      sectionRow.id = id;
      for(j in section) {
        sectionRow.children[j].innerHTML = section[j];
      }
      newChildTable.append(sectionRow);

      // Child was selected earlier - restore state
      if (selectedSections[sectionRow.id]) {
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

  // Instantiate table.;
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
      offset = expandedRows[calEvent.id.substring(0,9)].offsetTop;
      $('.dataTables_scrollBody').animate({ scrollTop: offset }, 500);
    },
  });

  // Used to store which courses have been selected and added to the calendar.
  selectedSections = JSON.parse(getCookie("selected") || "{}");
  for(id in selectedSections) {
    // TODO(alex) Rows selected here aren't added to expandedRows, and
    // the calendar events throw an error when clicked!
    data = selectedSections[id];
    createCalendarEvents(data.classTime, data.color, id);
  }

  function createCalendarEvents(classTime, color, id) {
    classTime.days.forEach(function(day) {
      var newEvent = {
        title: id.substr(0,9),
        start: `${day}T${classTime.start}`,
        end: `${day}T${classTime.end}`,
        color: color,
        id: id,
      }
      $('#calendar').fullCalendar('renderEvent', newEvent, true)
    });
  }

  function toggleSelected(dom_row) {
    child_row = $(dom_row);
    id = child_row.attr('id');
    dt = formatDays(child_row.children()[1].innerHTML);
    if(!selectedSections[id]) {
      color = getColor(child_row.children()[0].innerHTML)
      selectedSections[id] = {classTime: dt, color: color};
      $('#calendar').fullCalendar('removeEvents', id);
      createCalendarEvents(dt, color, id);
    } else {
      delete selectedSections[id];
      $('#calendar').fullCalendar('removeEvents', id);
    }
    setCookie("selected", JSON.stringify(selectedSections), 365);
    child_row.toggleClass('selected');
    dom_row.querySelector('input').checked = selectedSections[id];
  }

  function showChildRows(parent_row) {
    row = $(parent_row);
    row.toggleClass('shown');
    // Datatable row handle
    var row_handle = table.row(row);
    if (row_handle.child.isShown()) {
      // This row is already open - close it
      delete expandedRows[row_handle.data()[0]];
      row_handle.child.hide();
    }
    else {
      // Open this row
      expandedRows[row_handle.data()[0]] = parent_row;
      row_handle.child(createChild(parent_row), 'child-body').show();
      // TODO(Alex): There should be a better way to do this that
      // also fixes hovering over the table header without a color change.
      /*row_handle.child().hover(function(){
        $(this).css("background-color", "white");
      });*/
    }
  }

  $('#table tbody').on('mouseenter', 'tr', function(row) {
    row = $(row.currentTarget);
    if(row.hasClass("child-row")) {
      id = row.attr('id');
      dt = formatDays(row.children()[1].innerHTML);
      if(!selectedSections[id]) {
        createCalendarEvents(dt, '#AAA', id);
      }
    }
  });
  $('#table tbody').on('mouseleave', 'tr', function(row) {
    row = $(row.currentTarget);
    if(row.hasClass("child-row")) {
      id = row.attr('id');
      if(!selectedSections[id]) {
        $('#calendar').fullCalendar('removeEvents', id);
      }
    }
  });
  // Callback when parent row is opened or child row is selected.
  $('#table tbody').on('click', 'tr', function (e) {
    var row = $(this);
    if(row.hasClass("child-body")) {
      return;
    }
    else if(row.hasClass("child-row")) {
      toggleSelected(this);
    }
    else {
      showChildRows(this);
    }
  });

  $('#code-search').on('keyup change', function () {
    col = table.columns(0);
    if (col.search() !== this.value) {
      col.search(this.value).draw();
    }
  });

  $('#name-search').on('keyup change', function () {
    searchTerms.description = new RegExp(this.value, 'i');
    filterList.description.active = this.value != '';
    createFilters();
  });

  $('#instructor-search').on('keyup change', function () {
    searchTerms.instructor = new RegExp(this.value, 'i');
    filterList.instructor.active = this.value != '';
    createFilters();
  });

  function refreshTable() {
    for(id in expandedRows) {
      row = expandedRows[id];
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
});

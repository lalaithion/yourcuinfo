$(document).ready(function() {
  stateData = {
    selected: [],
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
      sectionRow = newChildTable.querySelector("tr").cloneNode(true);
      sectionRow.style.display = null;
      sectionRow.id = data.code + '-' + i;
      for(j in section) {
        sectionRow.children[j].innerHTML = section[j];
      }
      newChildTable.append(sectionRow);

      if(!stateData[sectionRow.id]) {
        stateData[sectionRow.id] = { 
          parentRow: parent_row,
          selected: false,
        }
      }
      else if (stateData[sectionRow.id].selected) {
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
    return [dates, start, end];
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
      offset = stateData[calEvent.id].parentRow.offsetTop;
      $('.dataTables_scrollBody').animate({ scrollTop: offset }, 500);
    },
  });

  // Used to store which courses have been selected and added to the calendar.
  var childFilters = [];
  var scookie = getCookie("selected");
  var selected = scookie ? JSON.parse(scookie) : {};

  drawCal = function(selected) {
    for (course in selected) {
      selected[course] = selected[course].map( function(instance) {
        var newID = $('#calendar').fullCalendar('renderEvent', instance, true)._id;
        instance.id = newID;
        return instance;
      });
    }
  }

  drawCal(selected)

  function createCalendarEvents(days, starttime, endtime, color, id) {
    days.forEach(function(day) {
      var newEvent = {
        title: id.substr(0,9),
        start: `${day}T${starttime}`,
        end: `${day}T${endtime}`,
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
    if(!stateData[id].selected) {
      stateData[id].selected = true;
      $('#calendar').fullCalendar('removeEvents', id);
      createCalendarEvents(dt[0], dt[1], dt[2], getColor(child_row.children()[0].innerHTML), id);
    } else {
      stateData[id].selected = null;
      $('#calendar').fullCalendar('removeEvents', id);
    }
    setCookie("selected", JSON.stringify(selected), 30);
    child_row.toggleClass('selected');
    dom_row.querySelector('input').checked = stateData[id].selected;
  }

  function showChildRows(parent_row) {
    row = $(parent_row);
    row.toggleClass('shown');
    // Datatable row handle
    var row_handle = table.row(row);
    if ( row_handle.child.isShown() ) {
      // This row is already open - close it
      row_handle.child.hide();
    }
    else {
      // Open this row
      row_handle.child(createChild(parent_row), 'child-body').show();
      row_handle.child().hover(function(){
        $(this).css("background-color", "white");
      });
    }
  }

  $('#table tbody').on('mouseenter', 'tr', function(row) {
    row = $(row.currentTarget);
    if(row.hasClass("child-row")) {
      id = row.attr('id');
      dt = formatDays(row.children()[1].innerHTML);
      if(!stateData[id].selected) {
        createCalendarEvents(dt[0], dt[1], dt[2], '#AAA', id);
      }
    }
  });
  $('#table tbody').on('mouseleave', 'tr', function(row) {
    row = $(row.currentTarget);
    if(row.hasClass("child-row")) {
      id = row.attr('id');
      if(!stateData[id].selected) {
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

  $('#code-search').on( 'keyup change', function () {
    col = table.columns(0);
    if ( col.search() !== this.value ) {
        col.search(this.value).draw();
    }
  });

  $('#name-search').on( 'keyup change', function () {
    col = table.columns(4)
    if ( col.search() !== this.value ) {
        col.search(this.value).draw();
    }
  });

  var filters = {
    "full": {
      parent: function( settings, data, dataIndex ) {
        return data[3] == "open";
      },
      child: function( id, data ) {
        return data[3] > 0;
      },
      active: false
    },
    "selected": {
      parent: function( settings, data, dataIndex ) {
        for (entry in selected) {
          if (entry.substring(0,9) == data[0]) {
            return true;
          }
        }
        return false;
      },
      child: function( id, data ) {
        for (entry in selected) {
          if (entry == id) {
            return true;
          }
        }
        return false;
      },
      active: false
    }
  };

  function createFilters() {
    $.fn.dataTable.ext.search = [];
    childFilters = [];
    for (entry in filters) {
      if (filters[entry].active) {
        $.fn.dataTable.ext.search.push(filters[entry].parent)
        childFilters.push(filters[entry].child)
      }
    }
    table.draw();
  }

  $('#display-full').change(function(target) {
    filters["full"].active = target.currentTarget.checked;
    createFilters();
  });

  $('#display-selected').change(function(target) {
    filters["selected"].active = target.currentTarget.checked;
    createFilters();
  });
});

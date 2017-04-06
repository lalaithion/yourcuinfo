/* Helper function that creates the child rows.
 *
 * Parameters:
 *   course (string): course name
 *   description (string): course description
 *   children (array[array[_]]): containins information for child rows:
 *     children[i][0] = Type (lecture, recitation, etc)
 *     children[i][1] = Date/time
 *     children[i][2] = Available seats
 *     children[i][3] = Waitlist
 *     children[i][4] = Instructor
 *     children[i][5] = Units
 *     children[i][6] = Room
 *   selected ( { "class ID": { title: string, start: string, end: string, color: string, id: string } } ): list of selected classes
 *   filters ( { "filter name": function filter(id, data) } ): List of filters
 */
function format ( course, description, children, selected, filters ) {
    header = `<div style="padding-left:25px">${description}</div>
    <table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">
    <thead><th>Type</th><th>Time</th><th>Seats</th><th>Waitlist</th><th>Instructor</th><th>Room</th><th></th></thead>`;

    body = children.map(
      function(n, i) {
        id = `${course}-${i}`;
        // Filter results
        for (i = 0; i < filters.length; i++) { if (!filters[i](id, n)) return; }
        return `<tr class="${selected[id] !== undefined ? "child selected" : "child" }" id="${id}">
          <td>${n[0]}</td>
          <td>${n[1]}</td>
          <td>${n[2]}</td>
          <td>${n[3]}</td>
          <td>${n[4]}</td>
          <td>${n[6]}</td>
          <td><input type="checkbox" onclick="$(this).parent.click" ${selected[id] !== undefined ? "checked=1" : "" }  ></td>
        </tr>`
      }).join('');

    footer = `</table>`;
    return header + body + footer;
}

/*
 * Turns a myCUinfo-style date/time ("TuTh 2:00-2:50") into a fullCalendar-style date/time ("2014-06-09T14:50"). If you have to dig through it I am very sorry.
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

$(document).ready(function() {
  // Instantiate calendar.
  $('#calendar').fullCalendar({
    header: {
      left: '',
      center: '',
      right: ''
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
    events: []
  });

  // Instantiate table.;
  var scrollPos = 0;
  var table = $('#table').DataTable({
    "ajax": "class_data.json",
    "scrollY": "500px",
    "scrollCollapse": true,
    "paging": false,
    "deferRender": true,
    'sDom': 't',
    "columns": [
      null,
      null,
      null,
      { "visible": false }
    ],
    // Used to avoid annoying scrolling bug
    "preDrawCallback": function (settings) {
      scrollPos = $('.dataTables_scrollBody')[0].scrollTop;
    },
    "drawCallback": function (settings) {
      $('.dataTables_scrollBody')[0].scrollTop = scrollPos;
    }
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

  // Callback when parent row is opened or child row is selected.
  $('#table tbody').on('click', 'tr', function (e) {
    // DOM row handle
    var tr = $(this).closest('tr');
    // Datatable row handle
    var row = table.row( tr );
    if(tr[0].className == "") return;
    if(tr[0].className.indexOf("child") != -1) {
      // This row is a child - add it to the calendar
      id = tr[0].id;
      dt = formatDays(tr[0].children[1].innerHTML);
      if (selected[id] == undefined) {
        selected[id] = dt[0].map(function (date) {
          var event = {
            title: id.substr(0,9),
            start: `${date}T${dt[1]}`,
            end: `${date}T${dt[2]}`,
            color: getColor( tr[0].children[0].innerHTML ),
          }
          event.id = $('#calendar').fullCalendar('renderEvent', event, true)[0]._id;
          return event;
        })
      } else {
        delete selected[id];
        $('#calendar').fullCalendar('removeEvents');
        drawCal(selected);
      }
      setCookie("selected", JSON.stringify(selected), 30);
      $(this).toggleClass('selected');
      this.cells[6].childNodes[0].checked = selected[id] !== undefined ? 1 : undefined;
    }
    else {
      tr.toggleClass('shown');
      if ( row.child.isShown() ) {
        // This row is already open - close it
        row.child.hide();
      }
      else {
        // Open this row
        var rowData = row.data();
        var course = rowData[0], description = rowData[3], children = rowData.slice(6);
        row.child( format(course, description, children, selected, childFilters) ).show();
        row.child().hover(function(){
          $(this).css("background-color", "white");
        });
      }
    }
  });

  $('#code-search').on( 'keyup change', function () {
    col = table.columns(0);
    if ( col.search() !== this.value ) {
        col.search(this.value).draw();
    }
  });
  $('#name-search').on( 'keyup change', function () {
    col = table.columns(3)
    if ( col.search() !== this.value ) {
        col.search(this.value).draw();
    }
  });

  var filters = {
    "full": {
      parent: function( settings, data, dataIndex ) {
        return data[2] == "open";
      },
      child: function( id, data ) {
        return data[2] > 0;
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

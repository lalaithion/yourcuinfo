// Helper function that creates the child rows.
function format ( d, selected, filters ) {
    header = `<div style="padding-left:25px"><i>Description:</i><br/>${d[3]}</div>
    <table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">
    <thead>
      <td>Type</td>
      <td>Time</td>
      <td>Seats</td>
      <td>Waitlist</td>
      <td>Instructor</td>
    </thead>`;

    children = d.slice(6).reduce( function(acc, n, i) {
      id = `${d[0]}-${i}`;
      for (i = 0; i < filters.length; i++) {
        if (!filters[i](id, n)) return acc;
      }
      return acc +
      `<tr class="${selected[id]!==undefined ? "child selected" : "child" }" id="${id}">
        <td>${n[0]}</td>
        <td>${n[1]}</td>
        <td>${n[2]}</td>
        <td>${n[3]}</td>
        <td>${n[4]}</td>
      </tr>`
    }, '');

    footer = `</table>`;
    return header + children + footer;
}

// Turns a myCUinfo-style date/time ("TuTh 2:00-2:50") into a fullCalendar-style date/time ("2014-06-09T14:50"). If you have to dig through it I am very sorry.
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
    height: 656,
    allDaySlot: false,
    editable: false,
    events: []
  });

  // Instantiate table.
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
      ]
  });

  // Used to store which courses have been selected and added to the calendar.
  var childFilters = [];
  var scookie = getCookie("selected");
  var selected = scookie ? JSON.parse(scookie) : {};

  for (course in selected) {
    selected[course] = selected[course].map( function(instance) {
      var newID = $('#calendar').fullCalendar('renderEvent', instance, true)._id;
      instance.id = newID;
      return instance;
    });
  }

  // Callback when parent row is opened or child row is selected.
  $('#table tbody').on('click', 'tr', function (e) {
    var tr = $(this).closest('tr');
    var row = table.row( tr );
    if(tr[0].className == "") return;
    if(tr[0].className.indexOf("child") != -1) {
      id = tr[0].id;
      dt = formatDays(tr[0].children[1].innerHTML);
      if (selected[id] == undefined) {
        selected[id] = dt[0].map(function (date) {
          var event = {
            title: `${id.substr(0,9)}`,
            start: `${date}T${dt[1]}`,
            end: `${date}T${dt[2]}`,
            color: getColor( tr[0].children[0].innerHTML ),
          }
          event.id = $('#calendar').fullCalendar('renderEvent', event, true)._id;
          return event;
        })
      } else {
        selected[id].forEach((event) => $('#calendar').fullCalendar( 'removeEvents', event.id ));
        delete selected[id];
      }
      setCookie("selected", JSON.stringify(selected), 30);
      $(this).toggleClass('selected');
    }
    else {
      if ( row.child.isShown() ) {
        // This row is already open - close it
        row.child.hide();
        tr.removeClass('shown');
      }
      else {
        // Open this row
        row.child( format(row.data(), selected, childFilters) ).show();
        row.child().hover(function(){
          $(this).css("background-color", "white");
        });
        tr.addClass('shown');
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
        console.log(data)
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

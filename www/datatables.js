function format ( d, selected, filter ) {
    // `d` is the original data object for the row
    // console.log(d)
    return `<i>Description:</i><br>
            <div style="padding-left:25px">${d[3]}</div>
            <table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">
            <thead>
              <td>Type</td>
              <td>Time</td>
              <td>Seats</td>
              <td>Waitlist</td>
              <td>Instructor</td>
            </thead>`+
    d.slice(6).reduce( function(acc, n, i) {
      id = `${d[0]}-${i}`;
      return acc +
      `<tr class="${selected[id]!=undefined ? "child selected" : "child" }" id="${id}">
        <td>${n[0]}</td>
        <td>${n[1]}</td>
        <td>${n[2]}</td>
        <td>${n[3]}</td>
        <td>${n[4]}</td>
      </tr>` }, '') +
    `</table>`;
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

$(document).ready(function() {
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

  var table = $('#table').DataTable({
    "ajax": "class_data.json",
    "scrollY": "500px",
    "scrollCollapse": true,
    "paging": false,
    "deferRender": true,
    // "bInfo" : false,
    'sDom': 't'
    // "bFilter": false
  });

  var selected = {};
  $('#table tbody').on('click', 'tr', function (e) {
    var tr = $(this).closest('tr');
    var row = table.row( tr );
    if(tr[0].className == "") return;
    if(tr[0].className.indexOf("child") != -1) {
      // return;
      id = tr[0].id;
      dt = formatDays(tr[0].children[1].innerHTML);
      // console.log(id, dt);
      if (selected[id] === undefined) {
        selected[id] = dt[0].map(function (date) {
          var event = $('#calendar').fullCalendar('renderEvent', {
            id: id,
            title: `${tr[0].id.substr(0,9)}`,
            start: `${date}T${dt[1]}`,
            end: `${date}T${dt[2]}`,
            color: getColor( tr[0].children[0].innerHTML ),
          }, true);
          return event[0];
        })
      } else {
        selected[id].forEach((event) => $('#calendar').fullCalendar( 'removeEvents', event._id));
        selected[id] = undefined;
      }

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
        // console.log(row)
        row.child( format(row.data(), selected) ).show();
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
    col = table.columns(1);
    if ( col.search() !== this.value ) {
        col.search(this.value).draw();
    }
  });
  $('#display-full').change(function(target) {
    if (target.target.checked) {
      $.fn.dataTable.ext.search.push(
        function( settings, data, dataIndex ) {
          return data[2] == "open";
          // return seats > 0;
        }
      );
    }
    else {
      $.fn.dataTable.ext.search.pop()
    }
    table.draw();
  });
  // $('#display-full').change(function(target) {
  //   search = target.target.checked ? '' : '0'
  //   col = table.columns(3);
  //   if ( col.search() !== this.value ) {
  //     col.search(search).draw();
  //   }
  //   table.draw();
  // });

} );

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

  days = [ { day: "Mo", date: "09" }, { day: "Tu", date: "10" }, { day: "We", date: "11" }, { day: "Th", date: "12" }, { day: "Fr", date: "13" } ];

  // Turns a myCUinfo-style date/time ("TuTh 2:00-2:50") into a fullCalendar-style date/time ("2014-06-09T14:50"). If you have to dig through it I am very sorry.
  function formatDays(classDays) {
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

  var table = $('#table').DataTable({
    "ajax": "class_data.txt",
    "scrollY": "400px",
    "scrollCollapse": true,
    "paging": false,
    "deferRender": true,
    // "bInfo" : false,
    'sDom': 't'
    // "bFilter": false
  });

  var selected = {};
  $('#table tbody').on('click', 'tr', function (e) {
    title = this.childNodes[0].innerHTML;
    dt = formatDays(this.childNodes[2].innerHTML);
    if (selected[title] === undefined) {
      selected[title] = dt[0].map(function (date) {
        var event = $('#calendar').fullCalendar('renderEvent', {
          title: title,
          start: `${date}T${dt[1]}`,
          end: `${date}T${dt[2]}`,
        }, true);
        return event[0];
      })
    } else {
      selected[title].forEach((event) => $('#calendar').fullCalendar( 'removeEvents', event._id));
      selected[title] = undefined;
    }

    $(this).toggleClass('selected');
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
          var seats = parseFloat( data[3] ) || 0;

          return seats > 0;
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

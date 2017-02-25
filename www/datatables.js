$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
		if($('#displayFull').is(":checked")) {
			return true;
		}
        var seats = parseInt( data[3] );
		if (seats > 0) {
			return true;
		}
		return false;
    }
);

$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
        var max = parseInt( $('#maxWaitlist').val(), 10 );
        if(isNaN(max)) {
			return true;
		}
        var seats = parseInt( data[3] );
        if(seats > 0) {
			return true;
		}
        var waitlist = parseInt( data[4] );
        if(waitlist < max) {
			return true;
		}
        return false;
    }
);

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
			defaultView: 'basicWeek',
			editable: false,
			events: [
				{
					title: 'Birthday Party',
					start: '2014-06-13T07:00:00'
				}
			]
	  });

    var selected = {};
    var table = $('#table').DataTable({
	      "ajax": "class_data.txt",
        "scrollY":        "300px",
        "scrollCollapse": true,
        "paging":         false,
        "deferRender": true,
        // "rowCallback": function( row, data ) {
        //     if ( $.inArray(data.DT_RowId, selected) !== -1 ) {
        //         $(row).addClass('selected');
        //         // console.log(data);
        //     }
        // }
    });
    $('#table tbody').on('click', 'tr', function (e) {
      var id = e.target.id;
      console.log(e)
      console.log(id)
      if (selected[this.id] === undefined) {
        var event = $('#calendar').fullCalendar('renderEvent', {
          title: "ji",//data[0],
          start: '2014-06-13T08:00:00'
        }, true);
        selected[this.id] = event.id;
        console.log("Adding: ", event.id, "at", this.id);
        // console.log(this)
      } else {
        console.log("Removing: ", selected[this.id]);
        $('#calendar').fullCalendar( 'removeEvents', selected[this.id]);
        selected[this.id] = undefined;
      }

      $(this).toggleClass('selected');
      console.log($(this))
    });

    $('#maxWaitlist').keyup( function() {
        table.draw();
    });
    $('#displayFull').change(function() {
		table.draw();
    });

} );

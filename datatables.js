$.fn.dataTable.ext.search.push(
    function( settings, data, dataIndex ) {
		if(!$('#displayFull').is(":checked")) {
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

var class_filter = [];
$.fn.dataTable.ext.search.push(
  function( settings, data, dataIndex ) {
    if(!class_filter.length) {
      return true;
    }
    return (class_filter.indexOf(data[0]) != -1);
  }
);

$(document).ready(function() {
    var table = $('#example').DataTable( {
	"ajax": "class_data.txt",
        "scrollY":        "400px",
        "scrollCollapse": true,
        "paging":         false,
        "deferRender": true,
        "dom": '<"toolbar">frtip'
    } );

    $('#example tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('selected');
    } );

    $("div.toolbar").html(`<div style="float: left;"><input type="checkbox" id="displayFull" style="margin-right: 5px;"/>Hide classes with no seats</div>`);

    $('#maxWaitlist').keyup( function() {
        table.draw();
    });
    $('#displayFull').change(function() {
		    table.draw();
    });
    $('#class-filter').keyup( function() {
      var classes = $('#class-filter').val();
      class_filter = [];
      $('#errors').html("");
      while(classes) {
        var dept = classes.match(/^\s*[a-zA-Z]{4}/);
        if(!dept) {
          $('#errors').html("Unable to parse:" + classes.substring(0, 10) + "...");
          break;
        }
        classes = classes.substring(dept[0].length);
        var code;
        while(code = classes.match(/^\s*([0-9]{4})[\s,&]*/)) {
          var name = dept[0] + " " + code[1];
          classes = classes.substring(code[0].length);
          class_filter.push(name);
        }
      }
      table.draw();
    });

} );

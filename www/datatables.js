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
    var table = $('#example').DataTable( {
	"ajax": "class_data.txt",
        "scrollY":        "300px",
        "scrollCollapse": true,
        "paging":         false,
        "deferRender": true,
    } );
    
    $('#maxWaitlist').keyup( function() {
        table.draw();
    });
    $('#displayFull').change(function() {
		table.draw();
    });
    
} );

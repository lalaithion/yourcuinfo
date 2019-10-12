function Calendar(identifier) {
    var calendar = $(identifier);
    calendar.fullCalendar({
        header: {
            left: '',
            center: '',
            right: '',
        },
        columnFormat: 'ddd',
        hiddenDays: [0, 6], // Hide weekends
        defaultDate: '2014-06-12',
        defaultView: 'agendaWeek',
        minTime: '08:00:00',
        maxTime: '20:00:00',
        height: 'auto',
        allDaySlot: false,
        editable: false,
        eventTextColor: 'white',
        events: [],
        eventClick: function(calEvent, jsEvent, view) {
            offset = table.row( function ( _, data ) {
                return data[0] == calEvent.id.substring(0, 9);
            }).node().offsetTop
            $('.dataTables_scrollBody').animate({
                scrollTop: offset
            }, 500);
        },
        eventMouseover: function(calEvent, jsEvent) {
            calEvent.oldz = $(this).css('z-index');
            $(this).css('z-index', 10000);
        },
        eventMouseout: function(calEvent, jsEvent) {
            $(this).css('z-index', calEvent.oldz || 1);
        },
        eventRender: function(event, element, view) {
            tooltipClass = event.startHr > 10 ? 'tooltiptext-top' : 'tooltiptext-bot';
            element.addClass('tooltip');
            element.append('<span class="tooltiptext ' + tooltipClass + '">' + event.tooltip + '</span>');
            element.css('overflow', 'visible');
        }
    });

    function getColor(course_code) {
        scales = {
            buff: chroma.scale(['4f5355', 'cfb36a']).mode('lab'),
            redyell: chroma.scale(['6B0C00', 'D4D454']),
            earth: chroma.scale(['6B0C00', 'BAA86D', '4E6C33']),
            earth2: chroma.scale(['6B0C00', '378B76']).mode('hsl'),
            purple: chroma.scale(['6B0C00', '2C1773']).mode('hsl').padding(-0.05),
        }
    
        function hashCode(str) {
            var hash = 5381, i, chr;
            if (str.length === 0) return hash;
            for (i = 0; i < str.length; i++) {
                chr   = str.charCodeAt(i);
                hash  = ((hash << 5) - hash) + chr;
                hash  = hash % 104729
            }
            return hash;
        }
    
        hash = hashCode(course_code);
        percent = Math.abs((hash % 1000) / 1000); // percent is between 0 and 1
        // create a color scale
        scale = scales.buff;
        // get the color from it
        color = scale(percent).hex();
        return color;
    }
    
    /*
    * Creates calendar events for a given section.
    */
    function createCalendarEvents(section, color) {
        color = color || '#999';//getColor(id);
        tooltip = getParentCourseCode(section) + '<br\><i>(' + section.room + ')</i>';
        bitDays = {
            1: '09',
            2: '10',
            4: '11',
            8: '12',
            16: '13',
        };
        var ret = [];
        for (bit in bitDays) {
            if (bit & section.days) {
                dayString = '2014-06-' + bitDays[bit];
                startString = zeroPad(Math.floor(section.start / 60), 2) + ':' + zeroPad(section.start % 60, 2)
                endString = zeroPad(Math.floor(section.end / 60), 2) + ':' + zeroPad(section.end % 60, 2)
                var newEvent = {
                    title: getParentCourseCode(section),
                    start: dayString + 'T' + startString,
                    end: dayString + 'T' + endString,
                    color: color,
                    startHr: section.start / 60,
                    tooltip: tooltip,
                }
                var id = calendar.fullCalendar('renderEvent', newEvent, true);
                ret.push(id);
            }
        }
        return ret; 
    }
    
    function removeEvents(section) {
        calendar.fullCalendar('removeEvents', section);
    }

    this.addSection = (section) => createCalendarEvents(section);
    this.removeSection = (section) => removeEvents(section);
    this.ghostSection = (section) => createCalendarEvents(section, '#AAA');
    this.clear = () => removeEvents();
}
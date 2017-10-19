$(document).ready(function() {
    data = {}

    state = {
        expandedRows: {},
        selectedSections: [],
        searchTerms: {
            // Bit flag meaning enable all days
            days: 31,
        },
    };

    /*
     * Unpacks data from server into easy-to-use dictionary.
     */
    function unpackData(course) {
        function unpackSection(section) {
            return {
                type: section[0],
                days: section[1],
                start: section[2],
                end: section[3],
                units: section[4],
                seats: section[5],
                waitlist: section[6],
                instr: section[7],
                room: section[8],
                info: section[9],
            };
        }
        return {
            description: course[0],
            sections: course.slice(1).map((s) => unpackSection(s)),
        };
    }

    /*
     * Retreives data for a section based on section id (e.g. CSCI 1300-3).
     */
    function getSectionData(id) {
        return data[id.slice(0,9)].data.sections[id.slice(10)]
    }

    /*
     * Pads number with leading zeroes.
     */
    function zeroPad(n, width) {
        n = n.toString();
        return n.length < width ? new Array(width - n.length + 1).join('0') + n : n;
    }

    /*
     * Converts from easy-to-compare bitmasks to human-readable strings.
     */
    function dayToString(dayBitmask) {
        const days = {
            1: 'Mo',
            2: 'Tu',
            4: 'We',
            8: 'Th',
            16: 'Fr'
        };
        var dayString = '';
        for (i in days) {
            if (dayBitmask & i) {
                dayString += days[i];
            }
        }
        return dayString;
    }

    /*
     * Converts from easy-to-compare minute counts to human-readable strings.
     */
    function time2Str(time) {
        hour = Math.floor(time / 60);
        minute = time % 60;
        suffix = 'AM';
        if (hour > 12) {
            hour = hour - 12;
            suffix = 'PM';
        }
        return hour + ':' + zeroPad(minute, 2) + suffix;
    }

    /*
     * Creates a child node with detailed information.
     */
    const childTemplate = document.getElementById('child-template');
    const sectionTemplate = document.getElementById('section-template');
    const types = {
        0: 'Lecture',
        1: 'Recitation',
        2: 'Lab',
        3: 'Semenar',
        4: 'PRA',
        5: 'Studio',
        6: 'DIS',
        7: 'IND',
        8: 'INT',
        9: 'Other',
        10: 'MLS',
        11: 'FLD',
        12: 'RSC',
        13: 'CLN',
        14: 'WKS',
    }
    function createChild(code, parent_row) {
        var childData = data[code].data;
        var newChild = childTemplate.cloneNode(true); // true for deep clone
        var newChildTable = newChild.querySelector("tbody");
        newChild.insertBefore(document.createTextNode(childData.description),
            newChild.firstChild);
        newChild.style.display = null;

        state.expandedRows[code] = {
            parentRow: parent_row
        };
        childData.sections.forEach(function(sec, i) {
            var id = code + '-' + i;
            state.expandedRows[code][id] = sec;
            for (filterName in filterList) {
                filter = filterList[filterName];
                if (filter.active && !filter.child(id, sec)) {
                    return;
                }
            }
            row = newChildTable.querySelector("tr").cloneNode(true);
            row.style.display = null;
            row.id = id;
            row.children[0].innerHTML = types[sec.type];
            date = dayToString(sec.days)
            time = time2Str(sec.start) + ' - ' + time2Str(sec.end)
            row.children[1].innerHTML = date + ' ' + time;
            row.children[2].innerHTML = sec.seats;
            row.children[3].innerHTML = sec.waitlist;
            row.children[4].innerHTML = sec.instr;
            row.children[5].innerHTML = sec.room;
            newChildTable.append(row);

            // Child was selected earlier - restore state
            if (state.selectedSections.indexOf(row.id) >= 0) {
                row.querySelector("input").checked = true;
                row.className += " selected";
            }
        });
        saveState();
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
        days = [
            {day: "Mo", date: "09"},
            {day: "Tu", date: "10"},
            {day: "We", date: "11"},
            {day: "Th", date: "12"},
            {day: "Fr", date: "13"},
        ];
        dates = days.reduce(function(acc, val) {
            return (classDays.indexOf(val.day) == -1) ? acc : acc.concat(`2014-06-${val.date}`);
        }, []);
        times = classDays.match(/(\d{1,2}):(\d{2})(.M) - (\d{1,2}):(\d{2})(.M)/);
        startHour = String(Number(times[1]) + ((times[3] == "PM" && times[1] != "12") ? 12 : 0));
        endHour = String(Number(times[4]) + ((times[6] == "PM" && times[4] != "12") ? 12 : 0));
        start = `${(startHour.length > 1)?'':'0'}${startHour}:${times[2]}`;
        end = `${(endHour.length > 1)?'':'0'}${endHour}:${times[5]}`;
        return {
            days: dates,
            start: start,
            end: end
        };
    }

    /*
     * Saves the current state variable as a cookie.
     */
    function saveState() {
        // https://www.w3schools.com/js/js_cookies.asp
        function setCookie(cname, cvalue, exdays) {
            var d = new Date();
            d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
            var expires = "expires=" + d.toUTCString();
            document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
        }
        cookie = ''//JSON.stringify(state);
        setCookie('state', cookie, 256);
    }

    /*
     * Restores the state variable from the saved cookie.
     */
    function restoreState() {
        function getCookie(cname) {
            var name = cname + "=";
            var decodedCookie = decodeURIComponent(document.cookie);
            var ca = decodedCookie.split(';');
            for (var i = 0; i < ca.length; i++) {
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
        cookie = getCookie('state');
        //console.log("Cookie:", cookie)
        if (cookie) {
            state = JSON.parse(cookie);
        }
    }

    /*
     * Instantiate table.
     */
    var scrollPos = 0;
    var table = $('#table').DataTable({
        ajax: 'data/class_data.json',
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
            {
                "render": function (code)  {
                    switch(code) {
                        case 0: return 'Open';
                        case 1: return 'Waitlisted';
                        case 2: return 'Closed';
                    };
                },
            },
            {
                "render": function (packedData, type, row, meta) {
                    rowNum = meta.row;
                    rowName = row[0];
                    data[rowName] = {
                        data: unpackData(packedData),
                        row: rowNum,
                    }
                    // Result not used
                    return 0
                },
                "visible": false,
            },
        ],
        // Used to avoid annoying scrolling bug
        preDrawCallback: function(settings) {
            scrollPos = $('.dataTables_scrollBody')[0].scrollTop;
        },
        drawCallback: function(settings) {
            $('.dataTables_scrollBody')[0].scrollTop = scrollPos;
        },
    });

    /* 
     * Instantiate calendar.
     */
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
            offset = state.expandedRows[calEvent.id.substring(0, 9)].parentRow.offsetTop;
            $('.dataTables_scrollBody').animate({
                scrollTop: offset
            }, 500);
        },
    });

    /*
     * Creates calendar events when given a day bitstring and start / end times.
     */
    function createCalendarEvents(days, start, end, color, id) {
        bitDays = {
            1: '09',
            2: '10',
            4: '11',
            8: '12',
            16: '13',
        };
        for (bit in bitDays) {
            if (bit & days) {
                dayString = '2014-06-' + bitDays[bit];
                startString = zeroPad(Math.floor(start / 60), 2) + ':' + zeroPad(start % 60, 2)
                endString = zeroPad(Math.floor(end / 60), 2) + ':' + zeroPad(end % 60, 2)
                var newEvent = {
                    title: id.substr(0, 9),
                    start: dayString + 'T' + startString,
                    end: dayString + 'T' + endString,
                    color: color,
                    id: id,
                }
                $('#calendar').fullCalendar('renderEvent', newEvent, true)
            }
        };
    }

    /*
     * Toggles child row on click.
     */
    function toggleSelected(domRow) {
        function getColor(type) {
            switch (type) {
                case "Lecture":
                    return "#774444";
                case "Recitation":
                    return "#447744";
                default:
                    return "grey";
            }
        }

        var childRow = $(domRow);
        var id = childRow.attr('id');
        var rowData = getSectionData(id);
        // Delete any existing events
        $('#calendar').fullCalendar('removeEvents', id);
        sectionIndex = state.selectedSections.indexOf(id);
        if (sectionIndex < 0) {
            color = getColor(childRow.children()[0].innerHTML)
            state.selectedSections.push(id);
            createCalendarEvents(rowData.days, rowData.start, rowData.end, color, id);
        } else {
            state.selectedSections.splice(sectionIndex, 1);
        }
        saveState();
        childRow.toggleClass('selected');
        domRow.querySelector('input').checked = sectionIndex < 0;
    }

    /*
     * Toggles parent row on click.
     */
    function toggleDetailedDescription(parent_row) {
        var row = $(parent_row);
        row.toggleClass('shown');
        var row_handle = table.row(row);
        var code = row_handle.data()[0];
        if (row_handle.child.isShown()) {
            delete state.expandedRows[code];
            row_handle.child.hide();
            saveState();
        } else {
            row_handle.child(createChild(code, parent_row), 'child-body').show();
            // TODO(Alex): There should be a better way to do this that
            // also fixes hovering over the table header without a color change.
            /*row_handle.child().hover(function(){
              $(this).css("background-color", "white");
            });*/
        }
    }

    /*
     * Creates calendar events on mouseover.
     */
    $('#table tbody').on('mouseenter', 'tr', function(row) {
      var row = $(row.currentTarget);
      if(row.hasClass("child-row")) {
        var id = row.attr('id');
        var sData = getSectionData(id);
        if(id && state.selectedSections.indexOf(id) < 0) {
          createCalendarEvents(sData.days, sData.start, sData.end, '#AAA', id);
        }
      }
    });

    $('#table tbody').on('mouseleave', 'tr', function(row) {
      var row = $(row.currentTarget);
      var id = row.attr('id');
      if(id && state.selectedSections.indexOf(id) < 0) {
        $('#calendar').fullCalendar('removeEvents', id);
      }
    });

    /*
     * Toggles rows on click.
     */
    $('#table tbody').on('click', 'tr', function(e) {
        var row = $(this);
        if (row.hasClass("child-body")) {
            return;
        } else if (row.hasClass("child-row")) {
            toggleSelected(this);
        } else {
            toggleDetailedDescription(this);
        }
    });    

    /*
    function toggleParentFilter(name, f) {
        toggleParentFilter.filters = toggleParentFilters.filters || {};

        if (toggleParentFilter.filters[name]) {
            del toggleParentFilter.filters[name];
        }
        else {
            toggleParentFilter.filters[name] = f;
        }

        $.fn.dataTable.ext.search = Object.values(toggleParentFilter.filters);
    }

    function toggleChildFilter(name, f) {
        
    }

    function filterFullClasses(_, d) {
        return d[3] == "Open";
    }

    function filterByDescription(_, d) {
        return 
    }*/
    var filterList = {
        full: {
            parentRow: function(settings, data, dataIndex) {
                return data[3] == "Open";
            },
            child: function(id, data) {
                return data.seats > 0;
            },
            active: false
        },
        description: {
            parentRow: function(settings, rowData, dataIndex) {
                var searchTerm = state.searchTerms.description;
                return rowData[1].search(searchTerm) >= 0 ||
                    data[rowData[0]].data.description.search(searchTerm) >= 0;
            },
            child: function() {
                return true;
            },
            active: false
        },
        instructor: {
            parentRow: function(settings, rowData, dataIndex) {
                sections = data[rowData[0]].data.sections;
                for (section of sections) {
                    if (section.instr.search(state.searchTerms.instructor) >= 0) {
                        return true;
                    }
                }
                return false;
            },
            child: function(childName, data) {
                return data.instr.search(state.searchTerms.instructor) >= 0;
            },
            active: false
        },
        selected: {
            parentRow: function(settings, data, dataIndex) {
                for (id of state.selectedSections) {
                    if (id.substring(0, 9) == data[0]) {
                        return true;
                    }
                }
                return false;
            },
            child: function(childName, data) {
                return state.selectedSections.indexOf(childName) != -1;
            },
            active: false
        },
        conflicting: {
            parentRow: function(settings, rowData, dataIndex) {
                sections = data[rowData[0]].data.sections;
                for (id of state.selectedSections) {
                    s = getSectionData(id);
                    for (section of sections) {
                        daysInCommon = s.days & section.days;
                        notSameTime = (s.end < section.start) || (section.end < s.start);
                        if (!daysInCommon || notSameTime) {
                            return true;
                        }
                    }
                    return false;
                }
                return true;
            },
            child: function(rowID, rowData) {
                if (state.selectedSections.indexOf(rowID) >= 0) {
                  return true;
                }
                for (id of state.selectedSections) {
                    s = getSectionData(id);
                    daysInCommon = s.days & rowData.days;
                    notSameTime = (s.end < rowData.start) || (rowData.end < s.start);
                    if(daysInCommon && !notSameTime) {
                          return false;
                    }
                }
                return true;
            },
            active: false
        },
        days: {
            parentRow: function(settings, rowData, dataIndex) {
                sections = data[rowData[0]].data.sections;
                for (section of sections) {
                    var disabledDays = ~state.searchTerms.days;
                    if (!(section.days & disabledDays)) {
                        return true;
                    }
                }
                return false;
            },
            child: function(rowID, data) {
                var disabledDays = ~state.searchTerms.days & 0x1F;
                return !(data.days & disabledDays);
            },
            active: true
        },
    };

    $('#code-search').on('keyup change', function() {
    console.log(data)
        col = table.columns(0);
        if (col.search() !== this.value) {
            col.search(this.value).draw();
        }
    });

    $('#name-search').on('keyup change', function() {
        state.searchTerms.description = new RegExp(this.value, 'i');
        filterList.description.active = this.value != '';
        saveState();
        createFilters();
    });

    $('#instructor-search').on('keyup change', function() {
        state.searchTerms.instructor = new RegExp(this.value, 'i');
        filterList.instructor.active = this.value != '';
        saveState();
        createFilters();
    });

    function refreshTable() {
        for (id in state.expandedRows) {
            row = state.expandedRows[id].parentRow;
            table.row(row).child(createChild(id, row), 'child-body');
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

    days = ['#mon', '#tue', '#wed', '#thu', '#fri'];
    for (i in days) {
        (function(i) {
            $(days[i])[0].checked = true;
            $(days[i]).change(function(target) {
                mask = 1 << i;
                state.searchTerms.days ^= mask;
                saveState();
                refreshTable();
            });
        })(i);
    }

    createFilters();
    restoreState();
});

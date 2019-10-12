function setSemesterTag() {
    var query = window.location.search.slice(1);
    
    var params = query.split('&').reduce((params, param) => {
        let [key, value] = param.split('=');
        if (value != undefined) {
            params[key] = decodeURIComponent(value.replace(/\+/g, ' '));
        }
        return params;
    }, {});

    var index = available_semesters.indexOf(params.semester) || available_semesters.length-1;

    state.semester = available_semesters[index].toLowerCase();
    semester = available_semesters[index];
    nextSemester = available_semesters[index+1];
    previousSemester = available_semesters[index-1];

    function setLink(ele, semester) {
      if (semester) {
        ele.href = '?semester=' + semester;
        ele.style.display = 'inline';
      }
    }
    setLink(document.getElementById('next-semester'), nextSemester);
    setLink(document.getElementById('previous-semester'), previousSemester);
    document.getElementById('semester').innerHTML = semester.replace('_', ' ');
}

$(document).ready(function() {
    var calendar = new Calendar('#calendar');

    /*
     * Creates a child node with detailed information.
     */
    const childTemplate = document.getElementById('child-template');
    const sectionTemplate = document.getElementById('section-template');
    function createChild(code, parent_row) {
        var childData = data[code].data;
        var newChild = childTemplate.cloneNode(true); // true for deep clone
        var newChildTable = newChild.querySelector('tbody');
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
            row = newChildTable.querySelector('tr').cloneNode(true);
            row.style.display = null;
            row.id = id;
            row.children[1].innerHTML = typeToString(sec.type);
            date = dayToString(sec.days)
            time = time2Str(sec.start) + ' - ' + time2Str(sec.end)
            row.children[2].innerHTML = date + ' ' + time;
            row.children[3].innerHTML = sec.seats;
            row.children[4].innerHTML = sec.waitlist;
            row.children[5].innerHTML = sec.instr;
            row.children[6].innerHTML = sec.room;
            row.children[7].innerHTML = sec.info ? sec.info : 'N/A';
            newChildTable.append(row);

            // Child was selected earlier - restore state
            if (state.selectedSections.indexOf(row.id) >= 0) {
                row.querySelector('input').checked = true;
                row.className += ' selected';
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
        cookie = JSON.stringify(state.selectedSections);
        setCookie('ycui_' + state.semester, cookie, 256);
    }

    /*
     * Restores the state variable from the saved cookie.
     */
    function restoreState() {
        function getCookie(cname) {
            var name = cname + '=';
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
            return '';
        }
        cookie = getCookie('ycui_' + state.semester);
        if (cookie) {
            state.selectedSections = JSON.parse(cookie);
            for (id of state.selectedSections) {
                createCalendarEvents(id, false);
            }
        }

    }

    /*
     * Instantiate table.
     */
    var scrollPos = 0;
    var table = $('#table').DataTable({
        ajax: {
          url: 'data/formatted/' + state.semester + '.json',
          dataSrc: function ( json ) {
              document.getElementById('updated').innerHTML = 'Last updated ' + json.updated
              return json.data;
          }
        },
	      language: {
            emptyTable: 'Loading...'
        },
        processing: true,
        scrollY: '500px',
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
                'render': function (code)  {
                    switch(code) {
                        case 0: return 'Open';
                        case 1: return 'Waitlisted';
                        case 2: return 'Closed';
                    };
                },
            },
            {
                'render': function (packedData, _, row, meta) {
                    rowCode = row[0];
                    rowName = row[1];
                    rowNum = meta.row;
                    data[rowCode] = {
                        data: unpackData(packedData),
                        name: rowName,
                        row: rowNum,
                    }
                    // Result not used
                    return 0
                },
                'visible': false,
            },
        ],
        // Used to avoid annoying scrolling bug
        preDrawCallback: function(settings) {
            scrollPos = $('.dataTables_scrollBody')[0].scrollTop;
        },
        drawCallback: function(settings) {
            $('.dataTables_scrollBody')[0].scrollTop = scrollPos;
        },
        initComplete: function(settings, json) {
            restoreState();
        }
    });

    /*
     * Toggles child row on click.
     */
    function toggleSelected(domRow) {
        var childRow = $(domRow);
        var id = childRow.attr('id');
        // Delete any existing events
        $('#calendar').fullCalendar('removeEvents', id);
        sectionIndex = state.selectedSections.indexOf(id);
        if (sectionIndex < 0) {
            state.selectedSections.push(id);
            createCalendarEvents(id, false);
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
        }
    }

    /*
     * Creates calendar events on mouseover.
     */
    $('#table tbody').on('mouseenter', 'tr', function(row) {
      var row = $(row.currentTarget);
      if(row.hasClass("child-row")) {
        var id = row.attr('id');
        if(id && state.selectedSections.indexOf(id) < 0) {
          createCalendarEvents(id, true);
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
});

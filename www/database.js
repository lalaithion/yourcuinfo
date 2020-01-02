
const available_semesters = ['Spring_2018', 'Summer_2018', 'Fall_2018', 'Spring_2019'];

const SECTION_TYPES = {
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

function deserialize(serialized_data) {
    var ret = {};
    for(course of serialized_data) {
        ret[course[0]] = unpackData(course);
    }
    return ret;
}

const data = deserialize(raw_data.data);

const state = {
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
function unpackData(course_data) {
    course = {
        code: course_data[0],
        name: course_data[1],
        description: course_data[4][0],
    }
    function unpackSection(section_data) {
        return {
            parent: course,
            type: section_data[0],
            days: section_data[1],
            start: section_data[2],
            end: section_data[3],
            units: section_data[4],
            seats: section_data[5],
            waitlist: section_data[6],
            instr: section_data[7],
            room: section_data[8],
            info: section_data[9],
            coursecode: name,
            conflictsWith: function (other_section) {
                days_in_common = this.days & other_section.days;
                different_times = (this.end < other_section.start) || (other_section.end < this.start);
                return days_in_common && !different_times;
            }
        };
    }
    course.sections = course_data[4].slice(1).map((s) => unpackSection(s));
    return course;
}

function getSectionsOfCourse(course_code) {
    return data[course_code].sections;
}

function getParentCourseCode(section) {
    return section.parent.code;
}

/*
* Retreives data for a section based on section id (e.g. CSCI 1300-3).
*/
function getSectionData(id) {
    return data[id.slice(0,9)].data.sections[id.slice(10)];
}

/*
* Retreives class name for a section based on section id (e.g. CSCI 1300-3).
*/
function getClassName(id) {
    return data[id.slice(0,9)].name;
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
* Converts from integer type enum to string representation.
*/
function typeToString(type) {
    types = {
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
    return types[type];
}
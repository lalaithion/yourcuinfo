import json, re, pdb

def parseMeet(meetsHTML):
    if not meetsHTML or "online" in meetsHTML or "CE Music Lesson" in meetsHTML:
        return (0,0,0,"TBA")
    # '<div class="meet">MW 2pm-3:15pm in <a href="http://www.colorado.edu/campusmap/map.html?bldg=KOBL" target="_blank">Koelbel Bldg-Leeds Sch of Bus 340</a></div>'
    day_re = '(M)?(T)?(W)?(Th)?(F)?(Sa)?(Su)?'
    time_re = '([\d:]+)([ap]m)-([\d:]+)([ap]m)'
    room_re = '(?:(?:<a href=.*>)(.*)(?:</a>)|(.*))'
    meets_re = '<div class="meet">%s %s(?: in |; )%s</div>' % (day_re, time_re, room_re)

    # meets_re = "([MWTThFSaSu]+) ([\d:]+)([ap]m)-([\d:]+)([ap]m)"
    meets = re.match(meets_re, meetsHTML)


    if not meets:
        print(meetsHTML)
        pdb.set_trace()
    # if not meetsHTML or re.match('\\s*TBA\\s*$', meetsHTML):
    #     return Time(0, 0, 0)

    # days, start, _, end  = meetsHTML.split(' ')
    # dayBitmask = 0
    # for day, bit in dayBits.items():
    #     if day in days:
    #         dayBitmask |= bit
    days = 0
    for i in range(1, 7):
        if meets.group(i):
            days |= 1 << i

    # days = meets.group(1).replace("Th", "H")
    # days = days.replace("M", "Mo").replace("T", "Tu").replace("W", "We") \
    #             .replace("H", "Th").replace("F", "Fr")

    def formatTime(oldTime, half):
        time_re = "(\d+):?(\d*)"
        t = re.match(time_re, oldTime)

        hour = int(t.group(1))
        minute = int(t.group(2) or 0)
        return hour * 60 + minute + (0 if half == "a" or hour is 12 else 720)
        # return "%s:%s%s" % (t.group(1), t.group(2), "AM" if half == "a" else "PM")

    startTime = formatTime(meets.group(8), meets.group(9) or meets.group(11))
    endTime = formatTime(meets.group(10), meets.group(11))
    return (days, startTime, endTime, meets.group(12) or "TBA")

def parseSeats(seatsHTML):
    seats_re = '(<strong>Maximum Enrollment</strong>: (\d+) / <strong>Seats Avail</strong>: (\d+)(<br><strong>Waitlist Total</strong>: (\d+), (.*))?)|' \
               '(<strong>Maximum Enrollment</strong> / <strong>Seats Avail</strong>: Varies by section)'
    seats_search = re.match(seats_re, seatsHTML)

    # max_enroll = seats_search.group(2)
    seats = int(seats_search.group(3))
    waitlist = int(seats_search.group(5) or 0)
    # enroll_method = seats_search.group(6)

    return (seats, waitlist)

def parseInstructors(instructorHTML):
    instr_re = '<div class="instructor-detail">(?:<a href=.*>)(.*)(?:</a>)</div>'
    return ",".join(re.findall(instr_re, instructorHTML))

    # def formatInstructor(instr_element):
    #     instr_re = '<a href=.*>(.*)</a>'
    #     instr = instr_element.get_attribute('innerHTML')
    #     instr_search = re.match(instr_re, instr)
    #     # If there's no link, the regex will match nothing and we can just return the entire innerHTML
    #     return instr_search.group(1) if instr_search else instr
    # section['instructors'] = list(map(formatInstructor, instructors))

# def encodeDate(dateTime):
#     # Bit hacks in Python? Madness!
#     # Reasoning: Less space, easier comparisons when finding conflicts.
#     dayBits = {
#         'Mo': 1 << 0,
#         'Tu': 1 << 1,
#         'We': 1 << 2,
#         'Th': 1 << 3,
#         'Fr': 1 << 4,
#     }
#
#     if not dateTime or re.match('\\s*TBA\\s*$', dateTime):
#         return Time(0, 0, 0)
#
#     days, start, _, end  = dateTime.split(' ')
#     dayBitmask = 0
#     for day, bit in dayBits.items():
#         if day in days:
#             dayBitmask |= bit
#
#     def encodeTime(time):
#         result = re.match('(\d{1,2}):(\d{2})?(AM|PM)', time)
#         hour = int(result.group(1))
#         minute = int(result.group(2)) if result.group(2) else 0
#         if result.group(3) == 'PM' and hour is not 12:
#             hour += 12
#         # Again, why numbers and not strings? Easier to transfer and compare.
#         return (hour * 60) + minute;
#
#     return Time(dayBitmask, encodeTime(start), encodeTime(end))

def main():
    # {'key': '1', 'code': 'ACCT 3220', 'title': 'Corporate Financial Reporting 1', 'crn': '26499', 'no': '001', 'total': '3', 'schd': 'LEC', 'stat': 'W', 'isCancelled': '', 'mpkey': '2026', 'meets': 'MW 2-3:15p', 'instr': 'F. Tice', 'start_date': '2019-01-14', 'end_date': '2019-05-02', 'srcdb': '2191'}
    with open('classes.json') as f:
        classes = json.loads(f.read())

    # '26499': {
    #     'key': '1',
    #     'inst': 'CUBLD',
    #     'stat': 'W',
    #     'mpkey': '2026',
    #     'hours': '3',
    #     'hours_min': '3',
    #     'gmods': 'LTR,NOC,PF4',
    #     'code': 'ACCT 3220',
    #     'section': '001',
    #     'crn': '26499',
    #     'title': 'Corporate Financial Reporting 1',
    #     'last_updated': 'Tue Nov 27 2018 00:18:22 GMT-0600 (CST)',
    #     'hours_text': '3 Credit Hour Lecture',
    #     'seats': '<strong>Maximum Enrollment</strong>: 65 / <strong>Seats Avail</strong>: 0<br/><strong>Waitlist Total</strong>: 4, Auto-Enroll',
    #     'grd': 'Student Option',
    #     'xlist': '',
    #     'campus': 'Boulder Main Campus',
    #     'instmode_html': 'In Person',
    #     'dates_html': '2019-01-14 through 2019-05-02',
    #     'restrict_info': 'Requires prerequisite of BASE 2104 (minimum grade D-).',
    #     'clssnotes': '',
    #     'description': 'First of a two-course sequence intended to provide students with increasedfluency in the language of business. Focuses on U.S. and international accounting concepts and methods that underlie financial statements and the related implications for interpreting financial accounting information.',
    #     'meeting_html': '<div class="meet">MW 2pm-3:15pm in <a href="http://www.colorado.edu/campusmap/map.html?bldg=KOBL" target="_blank">Koelbel Bldg-Leeds Sch of Bus 340</a></div>',
    #     'exams_html': '',
    #     'instructordetail_html': '<div class="instructor-detail"><a href="https://fcq.colorado.edu/scripts/broker.exe?_PROGRAM=fcqlib.fcqdata.sas&iname=Tice,Frances" target="_blank">Frances Tice</a></div>',
    #     'attributes': '',
    #     'law': '',
    #     'eval_links': '<a href="https://fcq.colorado.edu/scripts/broker.exe?_PROGRAM=fcqlib.fcqdata.sas&subj=ACCT&crse=3220" target="_blank">Course Evaluations</a><br/>',
    #     'books_html': '<a class="btn" target="_blank" href="https://www.cubookstore.com/booklist.aspx?catalogid=26499&uterm=Spring2019">PURCHASE BOOKS</a>',
    #     'linkedhtml': '',
    #     'all_sections': '<div class="course-sections" role="grid" aria-readonly="true"><div role="row"><div role="columnheader" scope="col">Class Nbr</div><div role="columnheader" scope="col">Section #</div><div role="columnheader" scope="col">Type</div><div role="columnheader" scope="col">Campus</div><div role="columnheader" scope="col">Meets</div><div role="columnheader" scope="col">Instructor</div><div role="columnheader" scope="col">Status</div><div role="columnheader" scope="col">Dates</div></div><a role="row" href="#" class="course-section" data-action="result-detail" data-group="code:ACCT 3220" data-srcdb="2191" data-key="crn:26499"><div role="rowheader" class="course-section-crn"><span class="header-text">Class Nbr: </span> 26499</div><div role="gridcell" class="course-section-section"><span class="header-text">Section #: </span> 001</div><div role="gridcell" class="course-section-schd"><span class="header-text">Type: </span> LEC</div><div role="gridcell" class="course-section-camp"><span class="header-text">Campus: </span> Main</div><div role="gridcell" class="course-section-mp"><span class="header-text">Meets: </span> MW 2-3:15p</div><div role="gridcell" class="course-section-instr"><span class="header-text">Instructor: </span> F. Tice</div><div role="gridcell" class="course-section-stat"><span class="header-text">Status: </span> Waitlisted</div><div role="gridcell" class="course-section-dates"><span class="header-text">Dates: </span> 01-14 to 05-02</div></a><a role="row" href="#" class="course-section" data-action="result-detail" data-group="code:ACCT 3220" data-srcdb="2191" data-key="crn:26500"><div role="rowheader" class="course-section-crn"><span class="header-text">Class Nbr: </span> 26500</div><div role="gridcell" class="course-section-section"><span class="header-text">Section #: </span> 002</div><div role="gridcell" class="course-section-schd"><span class="header-text">Type: </span> LEC</div><div role="gridcell" class="course-section-camp"><span class="header-text">Campus: </span> Main</div><div role="gridcell" class="course-section-mp"><span class="header-text">Meets: </span> MW 12:30-1:45p</div><div role="gridcell" class="course-section-instr"><span class="header-text">Instructor: </span> F. Tice</div><div role="gridcell" class="course-section-stat"><span class="header-text">Status: </span> Waitlisted</div><div role="gridcell" class="course-section-dates"><span class="header-text">Dates: </span> 01-14 to 05-02</div></a><a role="row" href="#" class="course-section" data-action="result-detail" data-group="code:ACCT 3220" data-srcdb="2191" data-key="crn:26501"><div role="rowheader" class="course-section-crn"><span class="header-text">Class Nbr: </span> 26501</div><div role="gridcell" class="course-section-section"><span class="header-text">Section #: </span> 003</div><div role="gridcell" class="course-section-schd"><span class="header-text">Type: </span> LEC</div><div role="gridcell" class="course-section-camp"><span class="header-text">Campus: </span> Main</div><div role="gridcell" class="course-section-mp"><span class="header-text">Meets: </span> MW 9:30-10:45a</div><div role="gridcell" class="course-section-instr"><span class="header-text">Instructor: </span> F. Tice</div><div role="gridcell" class="course-section-stat"><span class="header-text">Status: </span> Waitlisted</div><div role="gridcell" class="course-section-dates"><span class="header-text">Dates: </span> 01-14 to 05-02</div></a></div>',
    #     'srcdb': '2191'
    # }

    with open('details.json') as f:
        details = json.loads(f.read())


    formatted = {}
    for section in classes["results"]:
        code = section["code"]
        crn = section["crn"]
        print("On section: ", code)
        credits = details[crn]["hours"]
        status = { "A": 0, "W": 1, "F": 2 }[section["stat"]]

        if code not in formatted:
            formatted[code] = [
                code,
                section["title"],
                credits,
                status,
                [details[crn]["description"]],
            ]
        elif credits != formatted[code][2]:
            formatted[code][2] = "varies"
        elif status != formatted[code][3]:
            # As long as one section is open, the overall status is open
            formatted[code][3] = min(status, formatted[code][3])

        type = {
            "Lecture": 0, "Recitation": 1, "Laboratory": 2, "Seminar": 3, "Practicum": 4,
            "Study": 5, "Studies": 5, "Dissertation": 6, "Independent": 7, "Internship": 8, "Other": 9,
            "Section": 10, "Field": 11, "Research": 12, "Clinical": 13, "Workshop": 14, "Studio": 15
        }[details[crn]["hours_text"].split(" ")[-1]]
        days, start, end, room = parseMeet(details[crn]["meeting_html"])
        seats, waitlist = parseSeats(details[crn]["seats"])
        instructors = parseInstructors(details[crn]["instructordetail_html"])
        formatted[code][4].append(
            [type, days, start, end, credits, seats, waitlist, instructors, room]
        )


    '''
    OUTPUT FORMAT
    {
        "updated": "2018-03-30",
        "data": [
            ["CODE","NAME","CREDITS",STATUS,
                ["DESCRIPTION",
                    [TYPE,DAYS,START,END,"CREDITS",SEATS,WAITLIST,"INSTRUCTOR","ROOM"]
                ]
            ],
            [...]
        ]
    }
    CODE (string): Course code, e.g. "CSCI 2270"
    NAME (string): Course name, e.g. "Computer Science 2: Data Structures"
    CREDITS (string): Credits, e.g. "4" or "4-7"
    STATUS (int): Course status in the form open=0, waitlisted=1, closed=2
    DESCRIPTION: Plain text description
    TYPE (int): Class type enumerated from 0-15
    DAYS (int): Days as a bitstring, e.g. MWF = 0b10101 = 21
    START (int): Start time in minutes from 00:00
    END (int): End time in minutes from 00:00
    CREDITS (string): Credits, e.g. "4" or "4-7"
    SEATS (int): Number of open seats
    WAITLIST (int): Number of students on waitlist
    INSTRUCTOR (string): Instructor name
    ROOM (string): Room number
    '''

    with open('out.json', 'w') as f:
        f.write(json.dumps({
            "updated": "2018-11-27",
            "data": list(formatted.values())
        }, separators=(',', ':')))

    pdb.set_trace()

if __name__ == "__main__":
    main()

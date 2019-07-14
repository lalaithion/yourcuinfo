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
    days = 0
    for i in range(1, 7):
        if meets.group(i):
            days |= 1 << (i-1)

    def formatTime(oldTime, half):
        time_re = "(\d+):?(\d*)"
        t = re.match(time_re, oldTime)

        hour = int(t.group(1))
        minute = int(t.group(2) or 0)
        return hour * 60 + minute + (0 if "a" in half or hour is 12 else 720)

    startTime = formatTime(meets.group(8), meets.group(9) or meets.group(11))
    endTime = formatTime(meets.group(10), meets.group(11))
    return (days, startTime, endTime, meets.group(12) or "TBA")

def parseSeats(seatsHTML):
    seats_re = '(<strong>Maximum Enrollment</strong>: (\d+) / <strong>Seats Avail</strong>: (\d+)(<br><strong>Waitlist Total</strong>: (\d+), (.*))?)|' \
               '(<strong>Maximum Enrollment</strong> / <strong>Seats Avail</strong>: Varies by section)'
    seats_search = re.match(seats_re, seatsHTML)

    seats = int(seats_search.group(3))
    waitlist = int(seats_search.group(5) or 0)

    return (seats, waitlist)

def parseInstructors(instructorHTML):
    instr_re = '<div class="instructor-detail">(?:<a href=.*>)(.*)(?:</a>)</div>'
    return ",".join(re.findall(instr_re, instructorHTML))

def main():
    with open('classes.json') as f:
        classes = json.loads(f.read())

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

if __name__ == "__main__":
    main()

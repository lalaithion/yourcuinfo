import json, sys, re

class Status():
    OPEN = 0
    WAITLISTED = 1
    CLOSED = 2

class Time:
    def __init__(self, days, start, end):
        self.days = days
        self.start = start
        self.end = end

class Section:
    def __init__(self, typ, time, units, seats, wait, instr, room, info):
        self.typ = typ
        self.time = time
        self.units = units
        self.seats = seats
        self.wait = wait
        self.instr = instr
        self.room = room
        self.info = info

class Course:
    def __init__(self, dept, num, name, credits, status, sections):
        self.dept = dept
        self.num = num
        self.name = name
        self.credits = credits
        self.status = status
        self.sections = sections

def encodeDate(dateTime):
    # Bit hacks in Python? Madness!
    # Reasoning: Less space, easier comparisons when finding conflicts.
    dayBits = {
        'Mo': 1 << 0,
        'Tu': 1 << 1,
        'We': 1 << 2,
        'Th': 1 << 3,
        'Fr': 1 << 4,
    }

    if re.match('\\s*TBA\\s*$', dateTime):
        return Time(0, 0, 0)

    days, start, _, end  = dateTime.split(' ')
    dayBitmask = 0
    for day, bit in dayBits.items():
        if day in days:
            dayBitmask |= bit

    def encodeTime(time):
        result = re.match('(\d{1,2}):(\d{2})(AM|PM)', time)
        hour = int(result.group(1))
        minute = int(result.group(2))
        if result.group(3) == 'PM' and hour is not 12:
            hour += 12
        # Again, why numbers and not strings? Easier to transfer and compare.
        return (hour * 60) + minute;

    return Time(dayBitmask, encodeTime(start), encodeTime(end))

types = {
    'LEC': 0,
    'REC': 1,
    'LAB': 2,
    'SEM': 3,
    'PRA': 4,
    'STU': 5,
    'DIS': 6,
    'IND': 7,
    'INT': 8,
    'OTH': 9,
    'MLS': 10,
    'FLD': 11,
    'RSC': 12,
    'CLN': 13,
    'WKS': 14,
}

def parseSection(section):
    typ = types[section["code"].split('-')[1]]
    time = encodeDate(section["time"])
    units = section["units"]
    seats = int(section["seats"])
    if section["waitlist"] == "NA":
        wait = 0
    else:
        wait = int(section["waitlist"])
    instr = section["instructor"]
    room = section["room"]
    info = section.get("description", "")
    return Section(typ, time, units, seats, wait, instr, room, info)

def parseCourse(code, course):
    dept, num = code.split(' ')
    name = course["name"]

    sections = []
    for section in course["sections"]:
        sections.append(parseSection(section))

    if len(sections) is 0:
        return Course(dept, num, name, 'N/A', Status.CLOSED, sections)


    minWaitlist = {}
    maxSeats = {}
    credits = sections[0].units
    for s in sections:
        minWaitlist[s.typ] = min(minWaitlist.get(s.typ, float("inf")), s.wait)
        maxSeats[s.typ] = max(maxSeats.get(s.typ, 0), s.seats)
        if s.units != credits:
            credits = 'varies'
    waitlist = max(minWaitlist.values())
    seats = min(maxSeats.values())

    status = Status.OPEN if seats != 0 else Status.WAITLISTED

    return Course(dept, num, name, credits, status, sections)

def parseCourseData(data):
    return [parseCourse(code, course) for code, course in data.items()]

def stringifyData(courses, catalog):
    courseData = []
    sectionData = []
    for c in courses:
        description = catalog.get(c.dept, {}).get(c.num, {}).get("body", None)
        if description != None:
            description = description.replace("\"", "\\\"")

        sections = []
        for s in c.sections:
            sections.append('[%d,%d,%d,%d,"%s",%d,%d,"%s","%s"%s]' %
                (s.typ, s.time.days, s.time.start, s.time.end, s.units,
                s.seats, s.wait, s.instr, s.room,
                ',"%s"' % s.info if s.info else ''))

        courseData.append('["%s %s","%s","%s",%d,["%s",%s]]' %
                (c.dept, c.num, c.name, c.credits, c.status, description, ','.join(sections)))

    return '{"data":[%s]}' % ','.join(courseData)

def main():
    newline = False
    with open('../data/json/mycuinfo.json') as data_file:
        courses = parseCourseData(json.load(data_file))
    with open('../data/json/catalog.json') as data_file:
        catalog = json.load(data_file)

    data = stringifyData(courses, catalog)

    with open('../data/class_data.json', 'w+') as out:
        out.write(data)


if __name__ == "__main__":
    main()

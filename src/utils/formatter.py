import json, sys, re

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
    if dateTime == 'TBA':
        return (0, 0, 0)
    days, start, _, end  = dateTime.split(' ')
    dayBitmask = 0
    for day, bit in dayBits.items():
        if day in days:
            dayBitmask |= bit
    
    def encodeTime(time):
        result = re.match('(\d{1,2}):(\d{2})(AM|PM)', time)
        hour = int(result.group(1))
        minute = int(result.group(2))
        if result.group(3) == 'PM':
            hour += 12
        # Again, why numbers and not strings? Easier to transfer and compare.
        return (hour * 60) + minute;

    return (dayBitmask, encodeTime(start), encodeTime(end))

def main():
    newline = False
    with open('../../docs/json/classes.json') as data_file:
        data = json.load(data_file)
    with open('../../docs/json/catalog.json') as data_file:
        courses = json.load(data_file)

    outfile = open('../../docs/class_data.json', 'w+')
    classes = []
    for department in data:
        for course in department.keys():
            sectionList = [];
            minWaitlist = {}
            maxSeats = {}
            credits = None
            for section_type in department[course]["sections"].keys():
                for section in department[course]["sections"][section_type]:
                    typ = section["type"]
                    days, start, end = encodeDate(section["time"])
                    room = section["room"]
                    seats = int(section["seats"])
                    if section["waitlist"] == "NA":
                        waitlist = 0
                    else:
                        waitlist = int(section["waitlist"])
                    instructor = section["instructor"]
                    if credits == None:
                        credits = section["units"]
                    elif credits != section["units"]:
                        credits = "varies"
                    minWaitlist[section_type] = min(minWaitlist.get(section_type, float("inf")), waitlist)
                    maxSeats[section_type] = max(maxSeats.get(section_type, 0), seats)
                    sectionList.append('["%s",%d,%d,%d,%d,%d,"%s","%s"]' % (typ, days, start, end, seats, waitlist, instructor, room))
            if len(minWaitlist) > 0:
                dept, num = course.split(' ')
                code = course;
                name = department[course]["name"]
                description = courses.get(dept, {}).get(num, {}).get("body", None)
                if description != None:
                    description = description.replace("\"", "\\\"")
                waitlist = min(minWaitlist.values())
                seats = min(maxSeats.values())
                status = "open" if seats else "waitlisted"
                sections = ','.join(sectionList)
                classes.append('["%s","%s","%s","%s","%s",%d,%d,%s]' % (code, name, credits, status, description, seats, waitlist, sections))
    classList = ',\n'.join(classes)
    outfile.write('{{"data":[\n{0}\n]}}'.format(classList))


if __name__ == "__main__":
    main()

import json, sys

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
            # sections = []
            # outfile.write('["{0}", "{1}", {2}, "{3}"').format(code, name, units, status);
            sectionList = [];
            minWaitlist = {}
            maxSeats = {}
            credits = None
            for section_type in department[course]["sections"].keys():
                for section in department[course]["sections"][section_type]:
                    typ = section["type"]
                    time = section["time"]
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
                    # print(section_type.type)
                    # print(minWaitlist.get(section_type, float("inf")), waitlist)
                    minWaitlist[section_type] = min(minWaitlist.get(section_type, float("inf")), waitlist)
                    maxSeats[section_type] = max(maxSeats.get(section_type, 0), seats)
                    sectionList.append('["{0}","{1}",{2},{3},"{4}","{5}"]'.format(typ, time, seats, waitlist, instructor, room))
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
                classes.append('["{0}","{1}","{2}","{3}","{4}",{5},{6},{7}]'.format(code, name, credits, status, description, seats, waitlist, sections))
    classList = ',\n'.join(classes)
    outfile.write('{{"data":[\n{0}\n]}}'.format(classList))


if __name__ == "__main__":
    main()

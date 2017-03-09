import json, sys

def main():
    newline = False
    with open('../json/classes.json') as data_file:
        data = json.load(data_file)
    with open('../json/catalog.json') as data_file:
        courses = json.load(data_file)

    outfile = open('../class_data.json', 'w+')
    classes = []
    for department in data:
        for course in department.keys():
            # sections = []
            # outfile.write('["{0}", "{1}", {2}, "{3}"').format(code, name, units, status);
            sectionList = [];
            minWaitlist = {}
            maxSeats = {}
            for section_type in department[course]["sections"].keys():
                for section in department[course]["sections"][section_type]:
                    type = section["type"]
                    time = section["time"]
                    seats = int(section["seats"])
                    waitlist = int(section["waitlist"])
                    units = section["units"]
                    instructor = section["instructor"]
                    # print(section_type.type)
                    # print(minWaitlist.get(section_type, float("inf")), waitlist)
                    minWaitlist[section_type] = min(minWaitlist.get(section_type, float("inf")), waitlist)
                    maxSeats[section_type] = max(maxSeats.get(section_type, 0), seats)
                    sectionList.append('["{0}","{1}",{2},{3},"{4}","{5}"]'.format(type, time, seats, waitlist, instructor, units))
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
                classes.append('["{0}","{1}","{2}","{3}",{4},{5},{6}]'.format(code, name, status, description, seats, waitlist, sections))
    classList = ',\n'.join(classes)
    outfile.write('{{"data":[\n{0}\n]}}'.format(classList))

if __name__ == "__main__":
    main()

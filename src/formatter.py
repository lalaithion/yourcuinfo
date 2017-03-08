import json

def main():
    newline = False
    with open('../json/classes.json') as data_file:
        data = json.load(data_file)
    with open('../json/catalog.json') as data_file:
        courses = json.load(data_file)

    outfile = open('ajax_formatted_output.txt', 'w+')
    outfile.write('{"data":[\n')
    for department in data:
        for course in department.keys():
            for section_type in department[course]["sections"].keys():
                for section in department[course]["sections"][section_type]:
                    if newline:
                        outfile.write(',\n')
                    else:
                        newline = True
                    dept, num = course.split(' ')
                    code = course;
                    name = department[course]["name"] + ' ({0})'.format(section["type"])
                    time = section["time"]
                    seats = section["seats"]
                    waitlist = section["waitlist"]
                    units = section["units"]
                    description = courses.get(dept, {}).get(num, {}).get("body", "")
                    outfile.write('["{0}","{1}","{2}","{3}","{4}","{5}","{6}"]'.format(
                        code, name, time, seats, waitlist, units, description))
    outfile.write('\n]}')

if __name__ == "__main__":
    main()

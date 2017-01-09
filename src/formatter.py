import json

newline = False
with open('classes.json') as data_file:
    data = json.load(data_file)

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
                code = course;
                name = department[course]["name"] + ' ({0})'.format(section["type"])
                time = section["time"]
                seats = section["seats"]
                waitlist = section["waitlist"]
                units = section["units"]
                outfile.write('["{0}","{1}","{2}","{3}","{4}","{5}"]'.format(code, name, time, seats, waitlist, units))
outfile.write('\n]}')

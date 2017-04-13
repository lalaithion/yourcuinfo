#!/usr/local/bin/python3

from html.parser import HTMLParser
from string import printable
from time import strftime, gmtime
import json
from os import listdir
from os.path import isfile, join

class Section():
    def __init__(self,data):
        self.data = data
    def __getattr__(self,name):
        return self.data[name]
    def __repr__(self):
        rep = "Section:" + self.type + "," + self.time + ")"
        return rep
    def json(self):
        return self.data


class Course():
    def __init__(self,title):
        readable_title = "".join(filter(lambda x: x in printable, title))
        self.identifier = readable_title[:9] #CSCI 3155
        self.name = readable_title[12:] #Principles of Programming Languages
        # some of these will be empty lists for many classes
        self.sections = {
            "lectures":[],
            "recitations":[],
            "labs":[],
            "seminars":[],
            "labs":[],
            "pra":[],
            "other":[],
            "studios":[]
        }
    def add_section(self,data):
        if data["section"][-3:] == "LEC":
            data["type"] = "lecture"
            self.sections["lectures"].append(Section(data))
        elif data["section"][-3:] == "REC":
            data["type"] = "recitation"
            self.sections["recitations"].append(Section(data))
        elif data["section"][-3:] == "LAB":
            data["type"] = "lab"
            self.sections["labs"].append(Section(data))
        elif data["section"][-3:] == "SEM":
            data["type"] = "seminar"
            self.sections["seminars"].append(Section(data))
        elif data["section"][-3:] == "PRA":
            data["type"] = "pra"
            self.sections["pra"].append(Section(data))
        elif data["section"][-3:] == "STU":
            data["type"] = "studio"
            self.sections["studios"].append(Section(data))
        else:
            data["type"] = "other"
            self.sections["other"].append(Section(data))

    def __repr__(self):
        rep = "Course("
        rep += self.identifier + " - " + self.name
        num_sec = (self.sections["lectures"] + self.sections["recitations"] + self.sections["labs"]
                  + self.sections["seminars"] + self.sections["pra"] + self.sections["other"] + self.sections["studios"])
        rep += ", sections:" + str(num_sec)
        rep += ")"
        return rep
    def json(self):
        json = {
            "name":self.name,
            "sections":{
                k:[i.json() for i in v] for k,v in self.sections.items()
            }
        }
        return json

class MyHTMLParser(HTMLParser):
    def __init__(self,verbose = True):
        self.courses = []
        self.fields = {}
        self.current = None
        self.title = None
        self.verbose = verbose
        super(MyHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr == "id":
                if "win0divSSR_CLSRSLT_WRK_GROUPBOX2GP$" in value:
                    self.current = "title"
                if "MTG_CLASS_NBR$" in value:
                    self.current = "number"
                if "MTG_CLASSNAME$" in value:
                    self.current = "section"
                if "MTG_DAYTIME$" in value:
                    self.current = "time"
                if "MTG_ROOM$" in value:
                    self.current = "room"
                if "MTG_INSTR$" in value:
                    self.current = "instructor"
                if "MTG_TOPIC$" in value:
                    self.current = "dates"
                if "CU_CLS_RSL_WRK_CU_SSR_UNITS_RANGE$" in value:
                    self.current = "units"
                if "CU_CLS_RSL_WRK_CU_SSR_ENRL_RES$" in value:
                    self.current = "restriction"
                if "CU_CLS_RSL_WRK_CU_SSR_CNSNT_REQ$" in value:
                    self.current = "consent"
                if "CU_CLS_RSL_WRK_AVAILABLE_SEATS$" in value:
                    self.current = "seats"
                if "CU_CLS_RSL_WRK_WAIT_TOT$" in value:
                    self.current = "waitlist"

    def handle_endtag(self, tag):
        # at end of class
        if self.current == "waitlist":
            if self.verbose:
                if "title" in self.fields:
                    print(self.fields["title"] + ":")
                print("Class: " + self.fields["number"])
                print("Section: " + self.fields["section"])
                print("Time: " + self.fields["time"])
                print("Room: " + self.fields["room"])
                print("Instructor: " + self.fields["instructor"])
                print("Dates: " + self.fields["dates"])
                #print("Status: " + self.fields["status"])
                print("Units: " + self.fields["units"])
                print("Enrollment Restriction: " + self.fields["restriction"])
                print("Instructor Consent Required: " + self.fields["consent"])
                print("Available Seats: " + self.fields["seats"])
                print("Wait List Total: " + self.fields["waitlist"])
                print()
            self.courses[-1].add_section(self.fields)
            self.fields = {}
            self.current = None
        if self.current in self.fields:
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            # Filter out non-printable characters (note: find out why there are non-printable characters!?)
            printable_data = "".join(filter(lambda x: x in printable, data))
            self.fields[self.current] = printable_data
            if self.current == "title":
                self.courses.append(Course(printable_data))

    def json(self):
        return {i.identifier:i.json() for i in self.courses}


def jsonify(filename):
    assert(filename.endswith(".html"))
    with open(filename, "r") as f:
        parser = MyHTMLParser(False)
        parser.feed(f.read())
        return parser.json()

def jsonify_dir(dirpath):
    class_info = []
    for f in listdir(dirpath):
        filepath = join(dirpath, f)
        if isfile(filepath):
            if filepath.endswith(".html"):
                print("Reading file:", filepath)
                try:
                    info = jsonify(filepath)
                    if not info:
                        raise Exception("Unable to parse file")
                    class_info.append(info)
                except Exception as err:
                    errors = True
                    log.write("Error during parsing of {0}:\n  {1}\n".format(filepath, err))

        else:
            print("Reading dir:", filepath)
            class_info.extend(jsonify_dir(filepath))
    return class_info

def main():
    log = open("parse.log", 'a+')
    date = strftime("%Y-%m-%d", gmtime())
    log.write("{0}\n{1}: Beginning parse:\n".format(date, strftime("%H:%M", gmtime())))
    errors = False

    root = "../../mycuinfo_html/"
    classes = jsonify_dir(root)
    with open('../../json/classes.json', 'w') as outfile:
        json.dump(classes, outfile, indent=4, separators=(',', ': '))

    log.write("{0}: Parse finished\n".format(strftime("%H:%M", gmtime())))
    log.close()
    print("Parse finished with no errors" if not errors else "Parse finished with errors")

if __name__ == "__main__":
    main()

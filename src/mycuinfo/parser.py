#!/usr/local/bin/python3

import json
import logging
import re
from html.parser import HTMLParser
from string import printable
from time import strftime, gmtime
from os import listdir
from os.path import isfile, join

logFormatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

handlers = [
    # logging.FileHandler('../../docs/logs/mycuinfo.log'),
    logging.StreamHandler(),
]

for handler in handlers:
    handler.setFormatter(logFormatter)
    root_logger.addHandler(handler)

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
                k: [i.json() for i in v] for k,v in self.sections.items()
            }
        }
        return json

class MyCUInfoHTMLParser(HTMLParser):
    def __init__(self):
        self.courses = []
        self.fields = {}
        self.current_state = None
        self.title = None
        super(MyCUInfoHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr == "id":
                if re.search("win0divSSR_CLSRSLT_WRK_GROUPBOX2GP", value):
                    self.current_state = "title"
                if re.search("MTG_CLASS_NBR", value):
                    self.current_state = "number"
                if re.search("MTG_CLASSNAME", value):
                    self.current_state = "section"
                if re.search("MTG_DAYTIME", value):
                    self.current_state = "time"
                if re.search("MTG_ROOM", value):
                    self.current_state = "room"
                if re.search("MTG_INSTR", value):
                    self.current_state = "instructor"
                if re.search("MTG_TOPIC", value):
                    self.current_state = "dates"
                if re.search("CU_CLS_RSL_WRK_CU_SSR_UNITS_RANGE", value):
                    self.current_state = "units"
                if re.search("CU_CLS_RSL_WRK_CU_SSR_ENRL_RES", value):
                    self.current_state = "restriction"
                if re.search("CU_CLS_RSL_WRK_CU_SSR_CNSNT_REQ", value):
                    self.current_state = "consent"
                if re.search("CU_CLS_RSL_WRK_AVAILABLE_SEATS", value):
                    self.current_state = "seats"
                if re.search("^CU_CLS_RSL_WRK_WAIT_TOT", value):
                    self.current_state = "waitlist"
                if re.search("^CU_CLS_RSL_WRK_CU_SSR_WAITLIST", value):
                    self.current_state = "waitlist"
                if re.search("DERIVED_CLSRCH_DESCRLONG", value):
                    self.current_state = "description"

    def handle_endtag(self, tag):
        # the waitlist is the last tag in the class
        if self.current_state == "waitlist":
            # logging.debug("Title: " + self.fields["title"])
            # logging.debug("Class: " + self.fields["number"])
            # logging.debug("Section: " + self.fields["section"])
            # logging.debug("Time: " + self.fields["time"])
            # logging.debug("Room: " + self.fields["room"])
            # logging.debug("Instructor: " + self.fields["instructor"])
            # logging.debug("Dates: " + self.fields["dates"])
            # #logging.debug("Status: " + self.fields["status"])
            # logging.debug("Units: " + self.fields["units"])
            # logging.debug("Enrollment Restriction: " + self.fields["restriction"])
            # logging.debug("Instructor Consent Required: " + self.fields["consent"])
            # logging.debug("Available Seats: " + self.fields["seats"])
            # logging.debug("Wait List Total: " + self.fields["waitlist"])
            # logging.debug("Description: " + self.fields["description"])
            # logging.debug("Adding %s" % self.fields['title'])
            self.courses[-1].add_section(self.fields)
            self.fields = {}
            self.current_state = None
        if self.current_state in self.fields:
            self.current_state = None

    def handle_data(self, data):
        if self.current_state == "title":
            self.courses.append(Course(printable_data))
        elif self.current_state is not None:
            # Filter out non-printable characters (note: find out why there are non-printable characters!?)
            printable_data = "".join(filter(lambda x: x in printable, data))
            self.fields[self.current_state] = printable_data

    def json(self):
        return {i.identifier:i.json() for i in self.courses}


def jsonify(filename):
    assert(filename.endswith(".html"))
    with open(filename, "r") as f:
        logging.info("Parsing %s" % filename)
        parser = MyCUInfoHTMLParser()
        parser.feed(f.read())
        return parser.json()

def jsonify_dir(dirpath):
    class_info = []
    for f in listdir(dirpath):
        filepath = join(dirpath, f)
        if isfile(filepath):
            if filepath.endswith(".html"):
                try:
                    info = jsonify(filepath)
                    if not info:
                        raise Exception("Unable to parse file")
                    class_info.append(info)
                except Exception as err:
                    raise
                    errors = True
                    logging.info("Error during parsing of %s:\n  %s: %s\n" % (filepath, type(err), err))

        else:
            print("Reading dir:", filepath)
            class_info.extend(jsonify_dir(filepath))
    return class_info

def main(inpath="../../docs/raw_html/mycuinfo/", outpath='../../docs/json/classes.json'):
    date = strftime("%Y-%m-%d", gmtime())
    logging.info("Beginning parse")
    errors = False

    classes = jsonify_dir(inpath)
    with open(outpath, 'w') as outfile:
        json.dump(classes, outfile, indent=4, separators=(',', ': '))

    logging.info("Parse finished")
    print("Parse finished with no errors" if not errors else "Parse finished with errors")

if __name__ == "__main__":
    main()

#!/usr/local/bin/python3

import json
import logging
import re
from html.parser import HTMLParser
from string import printable
from time import strftime, gmtime
from os import listdir
from os.path import isfile, join

class Section():
    def __init__(self,data):
        self.data = data

    def __getattr__(self,name):
        return self.data[name]

    def json(self):
        return self.data


class Course():
    def __init__(self,title):
        self.identifier = title[:9] #CSCI 3155
        self.name = title[12:] #Principles of Programming Languages
        # some of these will be empty lists for many classes
        self.sections = []

    def add_section(self,data):
        self.sections.append(Section(data))

    def json(self):
        return {
            "name": self.name,
            "sections": [s.json() for s in self.sections],
        }

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
                    self.current_state = "code"
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
                if re.match("CU_CLS_RSL_WRK_WAIT_TOT", value):
                    self.current_state = "waitlist"
                if re.match("CU_CLS_RSL_WRK_CU_SSR_WAITLIST", value):
                    self.current_state = "waitlist"
                if re.search("DERIVED_CLSRCH_DESCRLONG", value):
                    self.current_state = "description"

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        # Filter out non-printable characters (note: find out why there are non-printable characters!?)
        printable_data = "".join(filter(lambda x: x in printable, data))
        if self.current_state == "title":
            self.courses.append(Course(printable_data))
            self.current_state = None
        elif self.current_state == "waitlist":
            self.fields["waitlist"] = printable_data
            self.courses[-1].add_section(self.fields)
            self.fields = {}
            self.current_state = None
        elif self.current_state is not None:
            self.fields[self.current_state] = printable_data
            self.current_state = None

    def json(self):
        return {i.identifier: i.json() for i in self.courses}


def jsonify(filename):
    assert(filename.endswith(".html"))
    with open(filename, "r") as f:
        logging.info("Parsing %s" % filename)
        parser = MyCUInfoHTMLParser()
        parser.feed(f.read())
        return parser.json()

def jsonify_dir(dirpath):
    class_info = {}
    for f in listdir(dirpath):
        filepath = join(dirpath, f)
        if isfile(filepath) and filepath.endswith(".html"):
            try:
                info = jsonify(filepath)
                if not info:
                    raise Exception("Unable to parse file")
                for k, v in info.items():
                    if k in class_info:
                        raise Exception("Two instances of %s found!" % k)
                    class_info[k] = v
            except Exception as err:
                raise
                errors = True
                logging.info("Error during parsing of %s:\n  %s: %s\n" % (filepath, type(err), err))

    return class_info

def parse(inpath, outpath):
    logging.info("Beginning parse.")

    classes = jsonify_dir(inpath)
    with open(outpath, 'w') as outfile:
        logging.info('Writing to %s' % outpath)
        json.dump(classes, outfile, indent=4, separators=(',', ': '))

    logging.info("Parse finished.")

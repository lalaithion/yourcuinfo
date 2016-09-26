#!/usr/local/bin/python3

from html.parser import HTMLParser
from string import printable
import departments_list


class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.fields = {}
        self.current = None
        self.title = False
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
            self.fields = {}
            self.current = None
        if self.current in self.fields:
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            # Filter out non-printable characters (note: find out why there are non-printable characters!?)
            self.fields[self.current] = "".join(filter(lambda x: x in printable, data))

#for i in departments_list.departments:
with open("csci.html") as f:
    parser = MyHTMLParser()
    parser.feed(f.read())

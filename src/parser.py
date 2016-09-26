#!/usr/local/bin/python3

from html.parser import HTMLParser

import departments_list


class MyHTMLParser(HTMLParser):

    def __init__(self):
        self.course = False
        super(MyHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        for i in attrs:
            if "win0divSSR_CLSRSLT_WRK_GROUPBOX2GP" in i[1]:
                self.course = True

    def handle_endtag(self, tag):
        if tag == "div":
            self.course = False

    def handle_data(self, data):
        if self.course:
            print(data)

for i in departments_list.departments:
    with open("../raw_html/" + date + "-" + current + ".html","r") as f:
        parser = MyHTMLParser()
        parser.feed(f.read())

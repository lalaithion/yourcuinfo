from html.parser import HTMLParser
from string import printable
from time import strftime, gmtime
from collections import defaultdict
import json
from os import listdir
from os.path import isfile, join

log = open("parse.log", 'a+')
errors = False

def format_title(inp):
    ls = inp.split(' ')
    label = ls[0]
    title = ' '.join(ls[2:])
    ls = label.split('-')
    dept = ls[0]
    number = ls[1]
    return dept, number, title

class Course():
    def __init__(self,data):
        self.data = data
    def __getattr__(self,name):
        return self.data[name]
    def __repr__(self):
        rep = "Class:" + self.type + "," + self.time + ")"
        return rep
    def json(self):
        return self.data


class MyHTMLParser(HTMLParser):
    def __init__(self,verbose = True):
        self.courses = []
        self.fields = {}
        self.current = None
        self.title = None
        self.verbose = verbose
        super(MyHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        clss = dict(attrs).get("class", None)
        if clss == "node-title":
            self.current = "title"
        if clss == "field-items":
            self.current = "body"

    def handle_endtag(self, tag):
        # at end of class
        if self.current == "body":
            if self.verbose:
                print("Class: " + self.fields["title"])
                print("Description: " + self.fields["body"])
                print()
            dept, number, title = format_title(self.fields["title"])
            self.fields["title"] = title
            self.fields["number"] = number
            self.fields["dept"] = dept
            self.courses.append(Course(self.fields))
            self.fields = {}
            self.current = None
        if self.current in self.fields:
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            printable_data = "".join(filter(lambda x: x in printable, data))
            self.fields[self.current] = printable_data

    def json(self):
        return {i.number:i.json() for i in self.courses}

def jsonify(filename):
    assert(filename.endswith(".html"))
    with open(filename, "r") as f:
        parser = MyHTMLParser(verbose=False)
        parser.feed(f.read())
        j = parser.json()
    return j

def jsonify_dir(dirpath):
    class_info = defaultdict(dict)
    last = ''
    for f in listdir(dirpath):
        filepath = join(dirpath, f)
        if isfile(filepath):
            if filepath.endswith(".html"):
                try:
                    info = jsonify(filepath)
                    if not info:
                        raise Exception("Unable to parse file")
                    dept = filepath.split('/')[-1].split('.')[0][:4]
                    class_info[dept].update(info)
                except Exception as err:
                    errors = True
                    log.write("Error during parsing of {0}:\n  {1}\n".format(filepath, str(err)))
        else:
            class_info.extend(jsonify_dir(filepath))
    return class_info

def main():
    date = strftime("%Y-%m-%d", gmtime())
    log.write("{0}\n{1}: Beginning parse:\n".format(date, strftime("%H:%M", gmtime())))
    errors = False

    root = "../catalog_html/" + date + "/"
    catalog = jsonify_dir(root)
    with open('../json/catalog.json', 'w') as outfile:
        json.dump(catalog, outfile, indent=4, separators=(',', ': '))
        
    log.write("{0}: Parse finished\n".format(strftime("%H:%M", gmtime())))
    print("Parse finished with no errors" if not errors else "Parse finished with errors")

if __name__ == "__main__":
    main()

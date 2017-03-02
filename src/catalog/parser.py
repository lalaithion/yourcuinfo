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
    date = strftime("%Y-%m-%d", gmtime())
    log = open("parse.log", 'a+')
    log.write("{0}\n{1}: Beginning parse:\n".format(date, strftime("%H:%M", gmtime())))
    errors = False

    root = "../catalog_html/" + date + "/"
    catalog = jsonify_dir(root)
    with open('../json/catalog.json', 'w') as outfile:
        json.dump(catalog, outfile)
        
    log.write("{0}: Parse finished\n".format(strftime("%H:%M", gmtime())))
    log.close()
    print("Parse finished with no errors" if not errors else "Parse finished with errors")

if __name__ == "__main__":
    main()

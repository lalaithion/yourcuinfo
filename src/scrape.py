#!/usr/bin/python3

from departments_list import departments
import logging

logFormatter = logging.Formatter('%(asctime)s (%(threadName)s): %(message)s', '%H:%M:%S')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handlers = [
    logging.FileHandler('../data/logs/mycuinfo.log'),
    logging.StreamHandler(),
]

for handler in handlers:
    handler.setFormatter(logFormatter)
    root_logger.addHandler(handler)

def main():
    #from catalog import crawler, parser
    #crawler.main(departments)
    #parser.main()

    from mycuinfo import crawler, parser
    html_path = "../data/raw_html/mycuinfo/"
    json_path = "../data/json/"
    crawler.crawl(departments, html_path, n_threads=5)
    parser.parse(html_path, json_path)
    #parser.main(logpath="../data/logs/mycuinfo-parse.log", inpath="../data/raw_html/mycuinfo/", outpath="../data/json/classes.json")


if __name__ == "__main__":
    main()

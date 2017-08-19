#!/usr/bin/python3

from departments_list import departments
import logging

logFormatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

handlers = [
    logging.FileHandler('../docs/logs/mycuinfo.log'),
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
    html_path = "../docs/raw_html/mycuinfo/"
    crawler.crawl(departments, html_path, n_threads=1)
    #parser.main(logpath="../docs/logs/mycuinfo-parse.log", inpath="../docs/raw_html/mycuinfo/", outpath="../docs/json/classes.json")


if __name__ == "__main__":
    main()

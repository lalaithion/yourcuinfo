#!/usr/bin/python3

import logging, sys, os, argparse, getpass

from datetime import date

from departments_list import departments
import mycuinfo.crawler
import mycuinfo.parser
import catalog.crawler
import catalog.parser

root = os.path.dirname(os.path.realpath(__file__))

def init_logging():
    logFormatter = logging.Formatter('%(asctime)s (%(threadName)s): %(message)s', '%H:%M:%S')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handlers = [
        logging.FileHandler(os.path.join(root, '../data/logs/mycuinfo.log')),
        logging.StreamHandler(),
    ]

    for handler in handlers:
        handler.setFormatter(logFormatter)
        root_logger.addHandler(handler)

def main():
    ap = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Scrape websites for yourCUinfo')
    ap.add_argument('--headless', action='store_true',
            help='Run program in headless mode.')

    ap.add_argument('--mycuinfo', action='store_true',
            help='Scrape and parse data from MyCUInfo.')
    ap.add_argument('--catalog', action='store_true',
            help='Scrape and parse data from the CU catalog.')

    ap.add_argument('--no-parse', action='store_true',
            help='Only scrape the data without parsing it.')
    ap.add_argument('--no-scrape', action='store_true',
            help='Only parse the data without scraping it.')

    ap.add_argument('-threads', type=int, action='store', default=5,
            help='Run the program with this many threads.')
    ap.add_argument('-login', type=str, action='store',
            help='Read credentials from a JSON file in the format:\n' \
                 '<username>\n' \
                 '<password>')
    ap.add_argument('-html-path', type=str, action='store',
            default='../data/raw/mycuinfo/',
            help='Path to store HTML after scrape.')
    ap.add_argument('-json-path', type=str, action='store',
            default='../data/parsed',
            help='Path to store JSON after parse.')
    ap.add_argument('-year', type=int, action='store',
            default=date.today().year,
            help='Year to scrape.')
    ap.add_argument('-semester', choices=['Fall', 'Spring', 'Summer'],
            action='store', default='Fall',
            help='Semester to scrape. One of: [Fall, Spring, Summer].')
    ap.add_argument('-campus', choices=['boulder', 'denver', 'colorado-springs'], action='store',
            default='boulder',
            help='Campus to scrape. One of: Boulder.')
    args = ap.parse_args()

    init_logging()

    html_path = os.path.join(root, args.html_path, '%s_%s/' % (args.semester.lower(), args.year))
    json_path = os.path.join(root, args.json_path)

    if args.mycuinfo:

        if not args.no_scrape:
            if args.login is None:
                user = input('User: ').strip('\n')
                passwd = getpass.getpass()
            else:
                with open(args.login) as f:
                    user = f.readline()
                    passwd = f.readline()

            options = mycuinfo.crawler.ScrapeOptions(
                    args.year, args.semester, args.campus,
                    html_path, args.threads, args.headless)
            mycuinfo.crawler.crawl(departments, user, passwd, options)
        if not args.no_parse:
            mycuinfo.parser.parse(html_path, os.path.join(json_path, 'mycuinfo/%s_%s.json' % (args.semester.lower(), args.year)))

    if args.catalog:
        if not args.no_scrape:
            catalog.crawler.crawl(departments, html_path, args.threads)
        if not args.no_parse:
            catalog.parser.parse(html_path, os.path.join(json_path, 'catalog.json'))


if __name__ == "__main__":
    main()

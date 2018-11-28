#!/usr/bin/python3

import logging, sys, os, argparse, getpass

from datetime import date

import classes_crawler, classes_parser
# import classes.parser
import catalog.crawler
import catalog.parser
import audit_crawler

root = os.path.dirname(os.path.realpath(__file__))

def init_logging(logging_level):
    logFormatter = logging.Formatter('%(asctime)s (%(threadName)s): %(message)s', '%H:%M:%S')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging_level)

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

    ap.add_argument('--classes', action='store_true',
            help='Scrape and parse data from MyCUInfo class search.')
    ap.add_argument('--catalog', action='store_true',
            help='Scrape and parse data from the CU catalog.')
    ap.add_argument('--audit', action='store_true',
            help='Scrape and parse data from the CU degree audits.')

    ap.add_argument('--no-parse', action='store_true',
            help='Only scrape the data without parsing it.')
    ap.add_argument('--no-scrape', action='store_true',
            help='Only parse the data without scraping it.')
    ap.add_argument('--no-save-raw', action='store_true',
            help='Parse the data immidiately without saving raw files.')

    ap.add_argument('-threads', type=int, action='store', default=5,
            help='Run the program with this many threads.')
    ap.add_argument('-login', type=str, action='store',
            help='Read credentials from a JSON file in the format:\n' \
                 '<username>\n' \
                 '<password>')
    ap.add_argument('-raw-path', type=str, action='store',
            default='../data/raw/',
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
    ap.add_argument('-logging', choices=['debug', 'warning', 'info'], action='store',
            default='info',
            help='Logging level. One of: [debug, warning, info].')
    args = ap.parse_args()

    init_logging({'debug': logging.DEBUG,
                  'warning': logging.WARNING,
                  'info': logging.INFO}[args.logging])

    raw_path = os.path.join(root, args.raw_path, '%s_%s/' % (args.semester.lower(), args.year))
    json_path = os.path.join(root, args.json_path)

    if not (args.audit or args.classes or args.catalog):
        logging.error("No target selected, must include one of [--audit, --classes, --catalog]")
        exit(1)

    logging.info("Starting scrape with options:")
    for attr in dir(args):
        if not callable(getattr(args, attr)) and not attr.startswith("__"):
            logging.info("\t%s: %s" % (attr, getattr(args, attr)))

    if args.audit:
        if args.login is None and (args.audit or args.classes):
            user = input('User: ').strip('\n')
            passwd = getpass.getpass()
        else:
            with open(args.login) as f:
                user = f.readline()
                passwd = f.readline()
        options = mycuinfo.audit_crawler.ScrapeOptions(
                    os.path.join(args.raw_path, 'audit/'), args.threads, args.headless)

        audit_crawler.crawl(departments, user, passwd, options)

    if args.classes:
        if not args.no_scrape:
            classes_crawler.crawl(args)
        if not args.no_parse:
            classes_parser.parse(args)

    if args.catalog:
        if not args.no_scrape:
            catalog.crawler.crawl(departments, raw_path, args.threads)
        if not args.no_parse:
            catalog.parser.parse(raw_path, os.path.join(json_path, 'catalog.json'))


if __name__ == "__main__":
    main()

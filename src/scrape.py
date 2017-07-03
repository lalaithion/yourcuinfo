#! python3

import fire

from departments_list import departments

class Scraper(object):
    def catalog(self):
        from catalog import crawler, parser
        crawler.main(departments)
        parser.main()

    def mcui(self, threads=15):
        from mycuinfo import crawler, parser
        # rest = departments[departments.index('PSCI')+1:]
        crawler.main(departments, n_threads=threads, logpath="../docs/logs/mycuinfo-scrape.log", filepath="../docs/raw_html/mycuinfo/")
        parser.main(logpath="../docs/logs/mycuinfo-parse.log", inpath="../docs/raw_html/mycuinfo/", outpath="../docs/json/classes.json")

    def all(self, threads=15):
        self.catalog()
        self.mcui(threads=threads)


if __name__ == "__main__":
    fire.Fire(Scraper)

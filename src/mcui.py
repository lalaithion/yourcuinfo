#! python3

import mycuinfo.crawler as crawler
import mycuinfo.parser as parser
from departments_list import test_departments

def mcui():
    crawler.main(test_departments)
    parser.main()
    
if __name__ == "__main__":
    mcui()

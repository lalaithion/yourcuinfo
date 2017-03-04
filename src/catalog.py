#! python3

import catalog.crawler as crawler
import catalog.parser as parser
from departments_list import test_departments

def catalog():
    crawler.main(test_departments)
    parser.main()
    
if __name__ == "__main__":
    catalog()

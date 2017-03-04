#! python3

import catalog.crawler as crawler
import catalog.parser as parser
from departments_list import departments

def catalog():
    crawler.main(departments)
    parser.main()
    
if __name__ == "__main__":
    catalog()

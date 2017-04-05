#! python3

import mycuinfo.crawler as crawler
import mycuinfo.parser as parser
from departments_list import departments

def mcui():
    rest = departments[departments.index('PSCI')+1:]
    crawler.main(rest)
    parser.main()
    
if __name__ == "__main__":
    mcui()

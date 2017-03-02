#! python3

import mycuinfo.crawler as mcui_crawler
from departments_list import departments

def mcui():
    mcui_crawler.main(departments)
    
def catalog():
    pass
    
if __name__ == "__main__":
    mcui()

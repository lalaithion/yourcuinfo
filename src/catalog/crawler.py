#! python3

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
from time import strftime, gmtime
import os
import errno

date = strftime("%Y-%m-%d", gmtime())
store = '../catalog_html/'
url = 'http://www.colorado.edu/catalog/2016-17/courses?subject='

def newDir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def main(depts):
    path = store + date + '/'
    newDir(path)
    for dept in depts:
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        driver.get(url + dept)
        i = 0
        while True:
            i += 1
            results = driver.find_element_by_id("cc-results")
            filepath = path + dept + str(i) + ".html"
            print(filepath)
            with open(filepath, 'wb') as f:
                f.write(driver.page_source.encode())
            time.sleep(1)
            try:
                link = driver.find_element_by_class_name("pager-next")
                link.click()
            except:
                break
        driver.close()

if __name__ == "__main__":
    main(["CHEM", "CSCI", "APPM"])

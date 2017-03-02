#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
from time import strftime, gmtime
import departments_list
import os
import errno

url = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT" # mycuinfo url
loginTimer = 7 # time for login to complete
searchTimer = 10 # time for search to complete
maxDropdownTimer = 15 # maximum time for dropdown to open

def login(ukeys, pkeys):
    driver = webdriver.Chrome()
    driver.get(url)
    username = driver.find_element_by_id("username")
    username.clear()
    username.send_keys(ukeys)
    passwd = driver.find_element_by_id("password")
    passwd.clear()
    passwd.send_keys(pkeys)
    passwd.send_keys(Keys.RETURN)
    return driver

def runSearch(driver, current):
    timer = 0
    maxTimer = 5
    while True:
        try:
            driver.find_element_by_link_text('Search for Classes').click()
            break
        except Exception:
            if timer <= maxTimer:
                time.sleep(1)
                timer += 1
            else:
                raise
            
    time.sleep(3)

    driver.switch_to_frame("ptifrmtgtframe")

    Select(driver.find_element_by_id("CLASS_SRCH_WRK2_INSTITUTION$31$")).select_by_value("CUBLD")
    time.sleep(1)
    Select(driver.find_element_by_id("CLASS_SRCH_WRK2_STRM$35$")).select_by_visible_text('Spring 2017 UC Boulder')
    time.sleep(1)
    Select(driver.find_element_by_id("SSR_CLSRCH_WRK_CAMPUS$0")).select_by_visible_text('Boulder Main Campus')
    time.sleep(1)
    driver.find_element_by_id("SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)
    driver.find_element_by_id("CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH").click()

def newDir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def main(depts):
    ukeys = input("User: ").strip('\n')
    pkeys = getpass.getpass()
    date = strftime("%Y-%m-%d", gmtime())
    filepath = "../mycuinfo_html/" + date + "/"
    newDir(filepath)
    log = open(filepath + "scrape.log", 'w+')
    log.write("{0}\n{1}: Beggining new data harvest\n".format(date, strftime("%H:%M", gmtime())))
    for current in depts:
        error = False
        try:
            driver = login(ukeys, pkeys)
        except Exception as err:
            log.write("Error logging in as {0}:\n  {1}\n".format(ukeys, err))
            driver.close()
            continue

        time.sleep(loginTimer)

        try:
            runSearch(driver, current)
        except Exception as err:
            log.write("Error getting to search for {0}:\n  {1}\n".format(current, err))
            driver.close()
            continue

        time.sleep(3)

        # wait for arrows to appear
        try:
            numCourses = driver.find_element_by_id("CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL")
        except Exception as err:
            log.write("Error expanding all arrows in {0}:\n  {1}\n".format(current, err))
            driver.close()
            continue

        time.sleep(10)

        try:
            with open(filepath + current + ".html", 'w') as f:
                f.write(driver.page_source)
                f.close()
        except Exception as err:
            log.write("Error saving {0} to file:\n  {1}\n".format(current, err))

        driver.close()

    log.write("{0}: Finished data harvest\n".format(strftime("%H:%M", gmtime())))
    log.close()

if __name__ == "__main__":
    main(["CHEM", "APPM", "CSCI"])

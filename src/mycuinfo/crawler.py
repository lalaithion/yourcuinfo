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
login_timer = 10 # time for login to complete
expand_timer = 2 # time for dropdown arrows to open

def find_elem(driver_func, name, max_timer = 15):
    timer = 0
    while True:
        try:
            item = driver_func(name)
            return item
        except Exception as err:
            if timer <= max_timer:
                time.sleep(1)
                timer += 1
                continue
            else:
                raise err
    

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
    find_elem(driver.find_element_by_link_text, 'Search for Classes').click()

    time.sleep(1)

    find_elem(driver.switch_to_frame, "ptifrmtgtframe")

    time.sleep(1)

    Select(
        find_elem(driver.find_element_by_id, "CLASS_SRCH_WRK2_INSTITUTION$31$")
    ).select_by_value("CUBLD")
    
    time.sleep(1)
    
    Select(
        find_elem(driver.find_element_by_id, "CLASS_SRCH_WRK2_STRM$35$")
    ).select_by_visible_text('Fall 2017 UC Boulder')
    
    time.sleep(1)
    
    Select(
        find_elem(driver.find_element_by_id, "SSR_CLSRCH_WRK_CAMPUS$0")
    ).select_by_visible_text('Boulder Main Campus')
    
    time.sleep(1)

    find_elem(driver.find_element_by_id,"SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)
    
    time.sleep(1)
    
    find_elem(driver.find_element_by_id,"CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH").click()

def department(filepath, current, log, login_data):
    print(current)
    try:
        driver = login(login_data["uname"], login_data["pswd"])
    except Exception as err:
        log.write("Error logging in as {0}:\n  {1}\n".format(login_data["uname"], err))
        driver.close()
        raise err

    try:
        runSearch(driver, current)
    except Exception as err:
        log.write("Error getting to classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        raise err

    try:
        find_elem(driver.find_element_by_id, "CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL").click()
    except Exception as err:
        log.write("Error exapnding classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        raise err

    time.sleep(expand_timer)

    try:
        with open(filepath + current + ".html", 'w') as f:
            f.write(driver.page_source)
            f.close()
    except Exception as err:
        log.write("Error saving {0} to file:\n  {1}\n".format(current, err))

    driver.close()

def main(depts):
    ukeys = input("User: ").strip('\n')
    pkeys = getpass.getpass()
    login = {"uname": ukeys, "pswd": pkeys}
    
    filepath = "../mycuinfo_html/"

    date = strftime("%Y-%m-%d", gmtime())
    log = open(filepath + "scrape.log", 'w+')
    log.write("{0}\n{1}: Beggining new data harvest\n".format(date, strftime("%H:%M", gmtime())))

    error = False
    for current in depts:
        try:
            department(filepath, current, log, login)
        except Exception as err:
            error = True
            continue

    log.write("{0}: Finished data harvest\n".format(strftime("%H:%M", gmtime())))
    log.close()

    if error:
        print("Scrape finished with Errors")
    else:
        print("!!! Scrape finished with Errors !!!")

if __name__ == "__main__":
    main(["CHEM", "APPM", "CSCI"])

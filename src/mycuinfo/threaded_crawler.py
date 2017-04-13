#!/usr/bin/python3

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
from time import strftime, gmtime
import os
import errno
import threading

url = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT" # mycuinfo url
n_threads = 10 # number of threads
login_timer = 20 # time for login to complete
expand_timer = 10 # time for dropdown arrows to open

def retry(func, action = None, max_timer = 30):
    timer = 0
    while timer < max_timer:
        try:
            x = func()
            return x
        except Exception:
            timer += 1
            time.sleep(1)
    raise Exception('Timeout: %s' % ('No description given' if action == None else action,))

def find_elem(driver_func, name, max_timer = 40):
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
                raise Exception("Timeout: Unable to find element %s" % (name,))


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

def click_elem(driver_func, name, max_timer = 40):
    elem = find_elem(driver_func, name, max_timer)
    timer = 0
    while True:
        try:
            elem.click()
            return
        except Exception as err:
            if timer <= max_timer:
                time.sleep(1)
                timer += 1
                continue
            else:
                raise Exception("Timeout: Unable to click element %s" % (name,))

def runSearch(driver, current, second_time=False):
    click_elem(driver.find_element_by_link_text, 'Search for Classes')

    find_elem(driver.switch_to_frame, "ptifrmtgtframe")

    retry(lambda: Select(
            find_elem(driver.find_element_by_id, "CLASS_SRCH_WRK2_INSTITUTION$31$")
        ).select_by_value("CUBLD"),
        action = 'Click class search')

    retry(lambda: Select(
            find_elem(driver.find_element_by_id, "CLASS_SRCH_WRK2_STRM$35$")
        ).select_by_visible_text('Fall 2017 UC Boulder'),
        action = 'Select year')

    time.sleep(1)

    retry(lambda: Select(
        find_elem(driver.find_element_by_id, "SSR_CLSRCH_WRK_CAMPUS$0")
    ).select_by_visible_text('Boulder Main Campus'),
        action = 'Select campus')

    time.sleep(1)

    find_elem(driver.find_element_by_id,"SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)

    time.sleep(1)

    # Chem has too many classes! AAAAAH
    if current == "CHEM":
        if second_time:
            Select(
                find_elem(driver.find_element_by_id, "SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2")
            ).select_by_visible_text("greater than or equal to")
        else:
            Select(
                find_elem(driver.find_element_by_id, "SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2")
            ).select_by_visible_text("less than or equal to")

        find_elem(driver.find_element_by_id, "SSR_CLSRCH_WRK_CATALOG_NBR$2").send_keys("3000")

    click_elem(driver.find_element_by_id, "CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH")


    # Check to see if the class search failed
    try:
        retry(lambda: driver.find_element_by_id("win0divDERIVED_CLSMSG_ERROR_TEXT"), max_timer=3)
    except:
        return
    raise Exception("Webpage reports error after class search (probably no results)")


def department(filepath, current, login_data, second_time=False):
    log = []
    # Login
    try:
        driver = login(login_data["uname"], login_data["pswd"])
    except Exception as err:
        log.append("Error logging in as {0}:\n  {1}\n".format(login_data["uname"], err))
        driver.close()
        return log

    # Search for department
    try:
        runSearch(driver, current, second_time)
    except Exception as err:
        log.append("Error getting to classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        return log

    # Open all dropdowns
    try:
        click_elem(driver.find_element_by_id, "CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL")
        # Wait for butten to take effect
        max_dropdown_timer = 20
        for seconds in range(max_dropdown_timer):
            try:
                driver.find_element_by_class_name("PTEXPAND_ARROW")
                time.sleep(1)
            except NoSuchElementException:
                break
        if seconds == max_dropdown_timer - 1:
            raise Exception("'Expand' arrows still exist on page after %d seconds" % (max_dropdown_timer))
    except Exception as err:
        log.append("Error exapnding classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        return log

    # Write results to file
    try:
        if second_time:
            current = current + '2'
        with open(filepath + current + ".html", 'w') as f:
            f.write(driver.page_source)
            f.close()
    except Exception as err:
        log.append("Error saving {0} to file:\n  {1}\n".format(current, err))
        driver.close()
        return log

    driver.close()

    # Loop for CHEM, as it's big enough to require two searches
    if current == "CHEM" and not second_time:
        log += department(filepath, current, login_data, True)

    return log

def redo(depts):
    ukeys = input("User: ").strip('\n')
    pkeys = getpass.getpass()
    login = {"uname": ukeys, "pswd": pkeys}

    filepath = "../mycuinfo_html/"

    date = strftime("%Y-%m-%d", gmtime())
    log = open(filepath + "scrape.log", 'w+')
    log.write("{0}\n{1}: Beggining new data harvest\n".format(date, strftime("%H:%M", gmtime())))

    error = False
    for current in depts:
        import os.path
        if os.path.isfile(filepath + current + '.html'):
            continue
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

def getDept(dept, filepath, login, results):
    log = department(filepath, dept, login)
    if len(log) > 0:
        results[dept] = '\n'.join(log)

def main(depts):
    ukeys = input("User: ").strip('\n')
    pkeys = getpass.getpass()
    login = {"uname": ukeys, "pswd": pkeys}

    filepath = "../../mycuinfo_html/"

    date = strftime("%Y-%m-%d", gmtime())
    log = open(filepath + "scrape.log", 'w+')
    log.write("{0}\n{1}: Beggining new data harvest\n".format(date, strftime("%H:%M", gmtime())))

    threads = []
    results = {}
    for current in depts:
        while len(threads) >= n_threads:
            [t.join() for t in threads if not t.isAlive()]
            threads = [t for t in threads if t.isAlive()]
            time.sleep(1)
        t = threading.Thread(target=getDept, args=(current, filepath, login, results,))
        t.start()
        threads.append(t)

    while len(threads):
        [t.join() for t in threads if not t.isAlive()]
        threads = [t for t in threads if t.isAlive()]
        time.sleep(1)

    errors = ['%s:\n%s' % (n, r) for n, r in results.items()]
    log.write('\n'.join(errors))
    log.write("{0}: Finished data harvest\n".format(strftime("%H:%M", gmtime())))
    log.close()

    if len(errors) == 0:
        print("Scrape finished with no Errors")
    else:
        print("!!! Scrape finished with Errors !!!")

if __name__ == "__main__":
    from departments_list import total_departments
    deps = total_departments
    main(deps)

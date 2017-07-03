#!/usr/bin/python3

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
import os
import errno
import threading

url = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT" # mycuinfo url
login_timer = 20 # time for login to complete
expand_timer = 10 # time for dropdown arrows to open
print_debug = False

def retry(f, *pargs, max_seconds=30, **kwargs):
    for i in range(max_seconds):
        try:
            return f(*pargs, **kwargs)
        except Exception:
            sleep(1)
    return f(*pargs, **kwargs)

def wait_until_fails(f, *pargs, max_seconds=15, **kwargs):
    try:
        for i in range(max_seconds):
            f(*pargs, **kwargs)
            sleep(1)
    except Exception:
        return True
    return False

def debug(m):
    if print_debug:
        print(m)

def wait_for_loading_icon():
    debug('Waiting for loading icon')
    if not wait_until_fails(deiver.find_elements_by_class_name, 'ui-icon-loading'):
        raise Exception("Loading icon did not vanish")

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


def runSearch(driver, current, second_time=False):
    debug('Clicking "search for classes"')
    search = retry(driver.find_element_by_link_text, 'Search for Classes').click()

    debug('Switching to main frame')
    retry(driver.switch_to_frame, "ptifrmtgtframe")

    debug('Selecting campus')
    Select(
        retry(driver.find_element_by_id, "CLASS_SRCH_WRK2_INSTITUTION$31$")
    ).select_by_value("CUBLD")

    wait_for_loading_icon()

    debug('Selecting semester')
    Select(
        retry(driver.find_element_by_id, "CLASS_SRCH_WRK2_STRM$35$")
    ).select_by_visible_text('Fall 2017 UC Boulder')

    wait_for_loading_icon()

    debug('Selecting campus')
    Select(
        retry(driver.find_element_by_id, "SSR_CLSRCH_WRK_CAMPUS$0")
    ).select_by_visible_text('Boulder Main Campus')

    wait_for_loading_icon()

    debug('Entering department')
    find_elem(driver.find_element_by_id,"SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)

    # Chem has too many classes! AAAAAH
    if current == "CHEM":
        debug('Splitting CHEM into two groups')
        if second_time:
            Select(
                retry(driver.find_element_by_id, "SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2")
            ).select_by_visible_text("greater than or equal to")
        else:
            Select(
                retry(driver.find_element_by_id, "SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2")
            ).select_by_visible_text("less than or equal to")

        wait_for_loading_icon()

        retry(driver.find_element_by_id, "SSR_CLSRCH_WRK_CATALOG_NBR$2").send_keys("3000")

    wait_for_loading_icon()

    debug('Submitting')
    retry(driver.find_elements_by_class_name, "gh-footer-item")[1].click()


def department(filepath, current, log, login_data, second_time=False):
    print(current)
    try:
        driver = login(login_data["uname"], login_data["pswd"])
    except Exception as err:
        log.write("Error logging in as {0}:\n  {1}\n".format(login_data["uname"], err))
        driver.close()
        raise err

    # time.sleep(login_timer)

    try:
        runSearch(driver, current, second_time)
    except Exception as err:
        log.write("Error getting to classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        raise err

    time.sleep(1)

    try:
        driver.find_element_by_id("win0divDERIVED_CLSMSG_ERROR_TEXT")
        return
    except:
        pass


    try:
        find_elem(driver.find_element_by_id, "CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL").click()
    except Exception as err:
        log.write("Error exapnding classes {0}:\n  {1}\n".format(current, err))
        driver.close()
        raise err

    time.sleep(expand_timer)

    try:
        if second_time:
            current = current + '2'
        with open(filepath + current + ".html", 'w') as f:
            f.write(driver.page_source)
            f.close()
    except Exception as err:
        log.write("Error saving {0} to file:\n  {1}\n".format(current, err))
        driver.close()
        raise err

    driver.close()

    if current == "CHEM" and not second_time:
        department(filepath, current, log, login_data, True)

def redo(depts):
        ukeys = input("User: ").strip('\n')
        pkeys = getpass.getpass()
        login = {"uname": ukeys, "pswd": pkeys}

        filepath = "../mycuinfo_html/"

        date = time.strftime("%Y-%m-%d", time.gmtime())
        log = open(filepath + "scrape.log", 'w+')
        log.write("{0}\n{1}: Beggining new data harvest\n".format(date, time.strftime("%H:%M", time.gmtime())))

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

        log.write("{0}: Finished data harvest\n".format(time.strftime("%H:%M", time.gmtime())))
        log.close()

        if error:
            print("Scrape finished with Errors")
        else:
            print("!!! Scrape finished with Errors !!!")

def main(depts, n_threads=15, logpath="../../docs/logs/mycuinfo.log", filepath="../../docs/raw_html/mycuinfo/"):
    ukeys = input("User: ").strip('\n')
    pkeys = getpass.getpass()
    login = {"uname": ukeys, "pswd": pkeys}

    start_date = time.strftime("%Y-%m-%d", time.gmtime())
    log = open(logpath, 'w')
    log.write("{0}\n{1}: Beggining new data harvest\n".format(start_date, time.strftime("%H:%M", time.gmtime())))

    error = False
    for current in depts:
        try:
            department(filepath, current, log, login)
        except Exception as err:
            raise err
            error = True
            continue

    log.write("{0}: Finished data harvest\n".format(time.strftime("%H:%M", time.gmtime())))
    log.close()

    if not error:
        print("Scrape finished with no Errors")
    else:
        print("!!! Scrape finished with Errors !!!")

class ThreadedWebInstance(object):
    def run():
        pass

if __name__ == "__main__":
    main()

#!/usr/bin/python3

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
import os
import errno
import threading
import queue
import logging
import traceback
import json

# Disable selenium logging.
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)

# URL of myCUinfo.
url = 'https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT'

# Retry action even if exception occurs.
def retry(f, *pargs, max_seconds=30, **kwargs):
    for i in range(max_seconds):
        try:
            return f(*pargs, **kwargs)
        except Exception as e:
            time.sleep(1)
    return f(*pargs, **kwargs)

# Wait for loading icon to vanish.
def wait_for_loading_icon(driver, max_seconds=5):
    SLEEP_INTERVAL = 0.5
    loading_icon = driver.find_elements_by_class_name('ui-icon-loading')[0]
    for i in range(int(max_seconds / SLEEP_INTERVAL)):
        if not loading_icon.is_displayed():
            return
        time.sleep(SLEEP_INTERVAL)
    raise Exception('Loading icon failed to disappear!')

# Log into myCUinfo.
def login(ukeys, pkeys):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver =  webdriver.Chrome(chrome_options=options)
    driver.get(url)
    logging.debug('Logging in')
    username = driver.find_element_by_id('username')
    username.clear()
    username.send_keys(ukeys)
    passwd = driver.find_element_by_id('password')
    passwd.clear()
    passwd.send_keys(pkeys)
    passwd.send_keys(Keys.RETURN)
    return driver

# Enter department info and search.
def runSearch(driver, current, second_time=False):
    logging.debug('Entering department: %s' % current)
    dept_element = retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SUBJECT$1')
    dept_element.clear()
    dept_element.send_keys(current)

    # Chem has too many classes! AAAAAH
    retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_CATALOG_NBR$2').clear()
    if current == 'CHEM':
        logging.debug('Splitting CHEM into two groups')

        course_code_text = ('greater' if second_time else 'less') + ' than or equal to'
        Select(
            retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2')
        ).select_by_visible_text(course_code_text)

        wait_for_loading_icon(driver)

        number = retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_CATALOG_NBR$2')
        number.send_keys('3000')

    wait_for_loading_icon(driver)

    logging.debug('Searching...')
    search = retry(driver.find_element_by_link_text, 'Search')
    retry(search.click)

# Search for department, save, and return to the search screen.
def scrape_department(driver, filepath, current, second_time=False):
    try:
        runSearch(driver, current, second_time)
    except Exception as err:
        logging.error('Error getting to classes %s:\n  %s\n' % (current, err))
        driver.close()
        raise err

    time.sleep(1)
    wait_for_loading_icon(driver, max_seconds=30)

    try:
        driver.find_element_by_id('win0divDERIVED_CLSMSG_ERROR_TEXT')
        logging.error('Got error message for %s, assumed empty.' % current)
        return
    except Exception as err:
        pass

    try:
        retry(driver.find_element_by_id, 'CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL').click()
    except Exception as err:
        logging.error('Error exapnding classes %s:\n  %s\n' % (current, err))
        driver.close()
        raise err

    logging.debug('Waiting for dropdowns to open.')
    timeout = 600
    for i in range(timeout):
        time.sleep(1)
        if not driver.find_elements_by_class_name('ui-icon-plus'):
            break

    time.sleep(10) # Just in case

    try:
        if second_time:
            current = current + '2'
        with open(filepath + current + '.html', 'w') as f:
            f.write(driver.page_source)
            f.close()
    except Exception as err:
        logging.error('Error saving %s to file:\n  %s\n' % (current, err))
        driver.close()
        raise err

    logging.debug('Going back to main search screen.')
    search = retry(driver.find_element_by_link_text, 'Modify Search', max_seconds=5)
    retry(search.click)

    if current == 'CHEM' and not second_time:
        scrape_department(driver, filepath, current, True)

def initDriver(login_data):
    driver = login(login_data['uname'], login_data['pswd'])

    logging.debug('Clicking "search for classes"')
    search = retry(driver.find_element_by_link_text, 'Search For Classes (standard)')
    retry(search.click)

    logging.debug('Switching to main frame')
    retry(driver.switch_to_frame, 'ptifrmtgtframe')

    institution = 'CUBLD'
    logging.debug('Selecting institution: %s' % institution)
    Select(
        driver.find_element_by_id('CLASS_SRCH_WRK2_INSTITUTION$31$')
    ).select_by_value(institution)

    wait_for_loading_icon(driver)

    semester = 'Spring 2018 UC Boulder'
    logging.debug('Selecting semester: %s' % semester)
    Select(
        driver.find_element_by_id('CLASS_SRCH_WRK2_STRM$35$')
    ).select_by_visible_text(semester)

    wait_for_loading_icon(driver)

    campus = 'Boulder Main Campus'
    logging.debug('Selecting campus: %s' % campus)
    Select(
        driver.find_element_by_id('SSR_CLSRCH_WRK_CAMPUS$0')
    ).select_by_visible_text(campus)

    wait_for_loading_icon(driver)

    return driver

def crawl(depts, filepath, n_threads, loginfile=None):
    logging.info('Beggining new data harvest')
    if loginfile is None:
        ukeys = input('User: ').strip('\n')
        pkeys = getpass.getpass()
        login = {'uname': ukeys, 'pswd': pkeys}
    else:
        with open(loginfile) as f:
            login = json.loads(f.read())

    departments = queue.Queue()
    for dept in depts:
        departments.put(dept)

    threads = []
    for i in range(n_threads):
        logging.info('Starting thread %d/%d.' % (i+1, n_threads))
        threads.append(QueuedThread(departments, filepath, login))
        threads[i].start()

    for i in range(n_threads):
        threads[i].join()

    logging.info('Finished data harvest.')

class QueuedThread(threading.Thread):
    def __init__(self, q, filepath, login):
        super(QueuedThread, self).__init__()
        self.dept_queue = q
        self.login = login
        self.filepath = filepath
        self.results = []

    def scrape(self, q, exception_handler=None):
        driver = initDriver(self.login)
        while not q.empty():
            dept = None
            try:
                dept = q.get_nowait()
                logging.info('Scraping department: %s.' % dept)
                self.results.append(scrape_department(driver, self.filepath, dept))
            except queue.Empty:
                continue
            except Exception as e:
                driver.close()
                if exception_handler is not None:
                    exception_handler(dept, e)
                    driver = initDriver(self.login)
                else:
                    raise
            finally:
                q.task_done()

    def run(self):
        failed_queue = queue.Queue()
        def exception_handler(dept, err):
            logging.info('Error in department %s: %s.' % (dept, err))
            failed_queue.put(dept)

        self.scrape(self.dept_queue, exception_handler)
        if not failed_queue.empty():
            logging.info('Retrying failed classes.')
            self.scrape(failed_queue)

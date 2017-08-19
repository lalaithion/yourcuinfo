#!/usr/bin/python3

from selenium import webdriver
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

logFormatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handlers = [
    logging.FileHandler('../../docs/logs/mycuinfo.log'),
    logging.StreamHandler(),
]

for handler in handlers:
    handler.setFormatter(logFormatter)
    root_logger.addHandler(handler)

url = 'https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT' # mycuinfo url
login_timer = 20 # time for login to complete
expand_timer = 10 # time for dropdown arrows to open

def retry(f, *pargs, max_seconds=30, **kwargs):
    for i in range(max_seconds):
        try:
            return f(*pargs, **kwargs)
        except Exception:
            time.sleep(1)
    return f(*pargs, **kwargs)

def wait_for_loading_icon(driver, max_seconds=5):
    SLEEP_INTERVAL = 0.5
    loading_icon = driver.find_elements_by_class_name('ui-icon-loading')[0]
    for i in range(int(max_seconds / SLEEP_INTERVAL)):
        if not loading_icon.is_displayed():
            return
        time.sleep(SLEEP_INTERVAL)
    raise Exception('Loading icon failed to disappear!')

def login(ukeys, pkeys):
    driver = webdriver.Chrome()
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

def runSearch(driver, current, second_time=False):
    logging.debug('Entering department')
    dept_element = retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SUBJECT$1')
    dept_element.clear()
    dept_element.send_keys(current)

    # Chem has too many classes! AAAAAH
    retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_CATALOG_NBR$2').clear()
    if current == 'CHEM':
        logging.debug('Splitting CHEM into two groups')
        if second_time:
            Select(
                retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2')
            ).select_by_visible_text('greater than or equal to')
        else:
            Select(
                retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2')
            ).select_by_visible_text('less than or equal to')

        wait_for_loading_icon(driver)
        retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_CATALOG_NBR$2').send_keys('3000')

    wait_for_loading_icon(driver)

    logging.debug('Submitting')
    search = retry(driver.find_element_by_link_text, 'Search')
    retry(search.click)

def scrape_department(driver, filepath, current, second_time=False):
    try:
        runSearch(driver, current, second_time)
    except Exception as err:
        logging.info('Error getting to classes %s:\n  %s\n' % (current, err))
        logging.info(traceback.format_exc())
        driver.close()
        raise err

    time.sleep(1)

    try:
        driver.find_element_by_id('win0divDERIVED_CLSMSG_ERROR_TEXT')
        logging.warning('Got error message for %s; aborting!' % current)
        return
    except:
        pass


    try:
        retry(driver.find_element_by_id, 'CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL').click()
    except Exception as err:
        logging.info('Error exapnding classes %s:\n  %s\n' % (current, err))
        driver.close()
        raise err

    time.sleep(expand_timer)

    try:
        if second_time:
            current = current + '2'
        with open(filepath + current + '.html', 'w') as f:
            f.write(driver.page_source)
            f.close()
    except Exception as err:
        logging.info('Error saving %s to file:\n  %s\n' % (current, err))
        driver.close()
        raise err

    logging.debug('Submitting')
    search = retry(driver.find_element_by_link_text, 'Modify Search', max_seconds=5)
    retry(search.click)

    if current == 'CHEM' and not second_time:
        scrape_department(driver, filepath, current, True)

def initDriver(login_data):
    try:
        driver = login(login_data['uname'], login_data['pswd'])
    except Exception as err:
        logging.info('Error logging in as %s' % (login_data['uname'], err))
        logging.info(traceback.format_exc())
        driver.close()
        raise

    logging.debug('Clicking "search for classes"')
    search = retry(driver.find_element_by_link_text, 'Search for Classes')
    retry(search.click)

    logging.debug('Switching to main frame')
    retry(driver.switch_to_frame, 'ptifrmtgtframe')

    logging.debug('Selecting institution')
    Select(
        driver.find_element_by_id('CLASS_SRCH_WRK2_INSTITUTION$31$')
    ).select_by_value('CUBLD')

    wait_for_loading_icon(driver)

    logging.debug('Selecting semester')
    Select(
        driver.find_element_by_id('CLASS_SRCH_WRK2_STRM$35$')
    ).select_by_visible_text('Fall 2017 UC Boulder')

    wait_for_loading_icon(driver)

    logging.debug('Selecting campus')
    Select(
        driver.find_element_by_id('SSR_CLSRCH_WRK_CAMPUS$0')
    ).select_by_visible_text('Boulder Main Campus')

    wait_for_loading_icon(driver)

    return driver

def main(depts, n_threads=1, filepath='../../docs/raw_html/mycuinfo/'):
    logging.info('Beggining new data harvest')
    ukeys = input('User: ').strip('\n')
    pkeys = getpass.getpass()
    login = {'uname': ukeys, 'pswd': pkeys}

    departments = queue.Queue()
    for dept in depts:
        departments.put(dept)

    threads = []
    for i in range(n_threads):
        threads.append(QueuedThread(departments, filepath, login))
        threads[i].start()

    for i in range(n_threads):
        threads[i].join()

    logging.info('Finished data harvest')

class QueuedThread(threading.Thread):
    def __init__(self, queue, filepath, login):
        super(QueuedThread, self).__init__()
        self.queue = queue
        self.login = login
        self.filepath = filepath
        self.results = []
        self.driver = initDriver(self.login)

    def run(self):
        while not self.queue.empty():
            try:
                dept = self.queue.get_nowait()
                self.results.append(scrape_department(self.driver, self.filepath, dept))
                self.queue.task_done()
            except queue.Empty:
                continue

if __name__ == '__main__':
    from departments_list import departments
    main(departments)

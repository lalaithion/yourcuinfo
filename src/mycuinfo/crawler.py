#!/usr/bin/python3

import time, os, errno, threading, queue, logging, traceback, json

import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER

# Disable selenium logging.
LOGGER.setLevel(logging.WARNING)

# URL of myCUinfo.
URL = 'https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT'
DEFAULT_TIMEOUT = 15

class ScrapeOptions():
    def __init__(self, year, semester, campus, data_path, threads, headless):
        self.year = year
        self.semester = semester
        self.campus = campus
        self.data_path = data_path
        self.threads = threads
        self.headless = headless

class MyCUInfoDriver():
    def __init__(self, username, password, options):
        self.driver = login(username, password, options.headless)
        self.options = options

    def find_id(self, i, timeout=DEFAULT_TIMEOUT):
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, i)))

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
def login(ukeys, pkeys, headless):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')

    driver =  webdriver.Chrome(chrome_options=options)
    driver.get(URL)
    logging.debug('Logging in')
    username = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'username')))
    # username = retry(driver.find_element_by_id, 'username')
    username.clear()
    username.send_keys(ukeys)
    passwd = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'password')))
    # passwd = retry(driver.find_element_by_id, 'password')
    passwd.clear()
    passwd.send_keys(pkeys)
    # passwd.send_keys(Keys.RETURN)
    return driver

# Enter department info and search.
def runSearch(driver, current, second_time=False):
    logging.debug('Entering department: %s' % current)
    dept_element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_SUBJECT$1')))
    # dept_element = retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_SUBJECT$1')
    dept_element.clear()
    dept_element.send_keys(current)

    # Chem has too many classes! AAAAAH
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_CATALOG_NBR$2'))).clear()
    # retry(driver.find_element_by_id, 'SSR_CLSRCH_WRK_CATALOG_NBR$2').clear()
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

def initDriver(username, password, options):
    driver = login(username, password, options.headless)

    logging.debug('Clicking "search for classes"')
    search = retry(driver.find_element_by_link_text, 'Search For Classes (Standard)')
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

def crawl(depts, options):
    logging.info('Beggining new data harvest')

    dept_queue = queue.Queue()
    for dept in depts:
        dept_queue.put((dept, 0))

    threads = []
    for i in range(options.threads):
        logging.info('Starting thread %d/%d.' % (i+1, options.threads))
        threads.append(CrawlerThread(dept_queue, username, password, options))
        threads[i].start()

    for i in range(options.threads):
        threads[i].join()

    logging.info('Finished data harvest.')

class CrawlerThread(threading.Thread):
    def __init__(self, dept_queue, username, password, options):
        super(CrawlerThread, self).__init__()
        self.dept_queue = dept_queue
        self.username = username
        self.password = password
        self.options = options
        self.results = {}

    def scrape(self, dept_queue, maxretry=2):
        driver = 
        while not dept_queue.empty():
            dept = None
            try:
                dept, count = dept_queue.get_nowait()
                self.results[dept] = scrape_department(driver, self.options.data_path, dept)
            except queue.Empty:
                continue
            except Exception as e:
                driver.quit()
                logging.info('Error in department %s: %s.' % (dept, e))
                if count < maxretry:
                    dept_queue.put((dept, count + 1))
                driver = initDriver(self.options)
            finally:
                dept_queue.task_done()

    def run(self):
        self.scrape(self.dept_queue)

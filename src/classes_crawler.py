#!/usr/bin/python3

import time, os, errno, threading, queue, logging, traceback, json, platform, datetime

from departments_list import departments
from classes_parser import html_to_json

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER

# Disable selenium logging.
LOGGER.setLevel(logging.WARNING)

HOME_URL = 'https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT'
DEFAULT_TIMEOUT = 15

def full_path(raw_path):
    return os.path.join(raw_path, 'classes/')

# Log into myCUinfo.
def login(ukeys, pkeys, headless):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')

    driver =  webdriver.Chrome(chrome_options=options)
    driver.get(HOME_URL)
    logging.debug('Logging in')

    username = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'username')))
    username.clear()
    username.send_keys(ukeys)

    passwd = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'password')))
    passwd.clear()
    passwd.send_keys(pkeys)

    # TODO: Figure out why these are different on different systems?
    if platform.system() != 'Linux':
        login = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'submit')))
        login.click()

    return driver


# Enter department info and search.
def runSearch(driver, args, current, second_time=False):
    options = [
        ('CLASS_SRCH_WRK2_INSTITUTION$31$', 'CU Boulder'),
        ('CLASS_SRCH_WRK2_STRM$35$', '{0.semester} {0.year} UC Boulder'.format(args)),
        ('SSR_CLSRCH_WRK_CAMPUS$0', 'Boulder Main Campus')
    ]

    for html_id, text in options:
        logging.debug('Setting %s to be %s' % (html_id, text))
        Select(WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, html_id)))
        ).select_by_visible_text(text)
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'ui-icon-loading')))

    logging.debug('Entering department: %s' % current)
    dept_element = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_SUBJECT$1')))
    dept_element.clear()
    dept_element.send_keys(current)

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_CATALOG_NBR$2'))).clear()

    # Chem has too many clases, so we're forced to split it up.
    if current == 'CHEM':
        logging.debug('Splitting CHEM into two groups')

        course_code_text = ('greater' if second_time else 'less') + ' than or equal to'
        Select(
            WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2')))
        ).select_by_visible_text(course_code_text)

        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'ui-icon-loading')))

        number = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'SSR_CLSRCH_WRK_CATALOG_NBR$2')))
        number.send_keys('3000')

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'ui-icon-loading')))

    logging.debug('Searching...')
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Search'))).click()

# Search for department, save, and return to the search screen.
def scrape_department(driver, args, current, second_time=False):
    try:
        runSearch(driver, args, current, second_time)
    except Exception as err:
        logging.error('Error getting to classes %s:\n  %s\n' % (current, err))
        driver.close()
        raise err

    time.sleep(1)
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'ui-icon-loading')))

    try:
        driver.find_element_by_id('win0divDERIVED_CLSMSG_ERROR_TEXT')
        logging.error('Got error message for %s, assumed empty.' % current)
        return
    except Exception as err:
        pass

    try:
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'CU_CLS_RSL_WRK_CU_SSR_EXPAND_ALL'))).click()
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

    try:
        if second_time:
            current = current + '2'

        if args.no_save_raw:
            with open(os.path.join(full_path(args.raw_path), current + '.json'), 'w') as f:
                f.write(json.dumps(html_to_json(driver.page_source)))
        else:
            with open(os.path.join(full_path(args.raw_path), current + '.html'), 'w') as f:
                f.write(driver.page_source)
    except Exception as err:
        logging.error('Error saving %s to file:\n  %s\n' % (current, err))
        driver.close()
        raise err

    logging.debug('Going back to main search screen.')
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.ID, 'submenu-button-0'))).click()
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Search for Classes'))).click()

    if current == 'CHEM' and not second_time:
        scrape_department(driver, args, current, second_time=True)

def initDriver(username, password, args):
    driver = login(username, password, args.headless)

    logging.debug('Clicking "search for classes"')
    for i in range(10):
        try:
            search = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Search For Classes (Standard)'))).click()
            break
        except WebDriverException:
            time.sleep(0.5)


    logging.debug('Switching to main frame')
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.frame_to_be_available_and_switch_to_it('ptifrmtgtframe'))

    return driver

def crawl(args):
    if args.login is None and (args.audit or args.classes):
        user = input('User: ').strip('\n')
        passwd = getpass.getpass()
    else:
        with open(args.login) as f:
            user = f.readline()
            passwd = f.readline()

    logging.info('Beggining new data harvest')

    path = full_path(args.raw_path)
    if not os.path.exists(path):
        os.makedirs(path)

    dept_queue = queue.Queue()
    for dept in departments:
        dept_queue.put((dept, 0))


    threads = []
    for i in range(args.threads):
        logging.info('Starting thread %d/%d.' % (i+1, args.threads))
        threads.append(CrawlerThread(dept_queue, user, passwd, args))
        threads[i].start()

    for i in range(args.threads):
        threads[i].join()

    logging.info('Finished data harvest.')

class CrawlerThread(threading.Thread):
    def __init__(self, dept_queue, username, password, args):
        super(CrawlerThread, self).__init__()
        self.dept_queue = dept_queue
        self.username = username
        self.password = password
        self.args = args
        self.maxretry = 3

    def run(self):
        driver = initDriver(self.username, self.password, self.args)
        while not self.dept_queue.empty():
            dept = None
            try:
                dept, count = self.dept_queue.get_nowait()
                logging.info('On %s.' % dept)
                scrape_department(driver, self.args, dept)
            except queue.Empty:
                continue
            except Exception as e:
                driver.quit()
                logging.error('Error in department %s: %s.' % (dept, e))
                if count < self.maxretry:
                    self.dept_queue.put((dept, count + 1))
                driver = initDriver(self.username, self.password, self.args)
            finally:
                self.dept_queue.task_done()

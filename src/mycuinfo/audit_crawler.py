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

import mycuinfo.utils

# Disable selenium logging.
LOGGER.setLevel(logging.WARNING)

# URL of myCUinfo.
URL = 'https://datc.prod.cu.edu/selfservice-cubld/audit/create.html'
DEFAULT_TIMEOUT = 15

class ScrapeOptions():
    def __init__(self, data_path="../data", threads=1, headless=False):
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

# Log into myCUinfo.
def login(ukeys, pkeys, headless):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')

    driver =  webdriver.Chrome(chrome_options=options)
    driver.get(URL)

    logging.debug('Logging in')

    username = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'username')))
    username.clear()
    username.send_keys(ukeys)

    passwd = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'password')))
    passwd.clear()
    passwd.send_keys(pkeys)

    # login = WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'submit')))
    # login.click()

    return driver

def initDriver(username, password, options):
    driver = login(username, password, options.headless)

    mycuinfo.utils.find_link_text(driver, 'Select a Different Program:').click()

    return driver

def crawl(depts, username, password, options):
    logging.info('Beggining new data harvest')

    if not os.path.exists(options.data_path):
        os.makedirs(options.data_path)

    program_queue = queue.Queue()
    program_queue.put((None, None, None, None))

    threads = []
    for i in range(options.threads):
        logging.info('Starting thread %d/%d.' % (i+1, options.threads))
        threads.append(CrawlerThread(username, password, program_queue, options))
        threads[i].start()

    program_queue.join()

    for i in range(options.threads):
        threads[i].done = True

    for i in range(options.threads):
        threads[i].join()

    logging.info('Finished data harvest.')

class CrawlerThread(threading.Thread):
    def __init__(self, username, password, program_queue, options):
        super(CrawlerThread, self).__init__()
        self.username = username
        self.password = password
        self.program_queue = program_queue
        self.options = options
        self.done = False

    def scrape(self):
        driver = initDriver(self.username, self.password, self.options)

        while not self.done:
            try:
                logging.debug("Queue size: %d" % self.program_queue.qsize())

                queue_head = self.program_queue.get_nowait()

                logging.debug("Selecting options")
                # For all possible options...
                options = list(queue_head)
                for i, ident in enumerate([
                        'degreeProgramCollege', 'degreeProgramDegree',
                        'whatIfDegreeProgram', 'catalogYearTerm']):
                    selector_element = mycuinfo.utils.find_id(driver, ident)
                    # Occationally a query doesn't provide a dropdown if there's only one option
                    # In that case, the selctor is displayed as a hidden <input> tag next to a <span> tag with the text we want
                    if selector_element.tag_name == 'input':
                        # Grab value of sibling span tag (yeah, this is really ugly)
                        sibling = driver.find_element_by_xpath("//input[@id='%s']/following-sibling::span" % ident)
                        options[i] = sibling.get_attribute('innerHTML')
                        continue
                    selector = Select(selector_element)

                    # ...if that particular option hasn't been read yet...
                    if options[i] is None:
                        # ...read options back into the queue for other threads to handle...
                        for opt in selector.options[1:-1]:
                            options[i] = opt.text
                            self.program_queue.put(tuple(options))
                        # ...and read the last option for the current thread to handle.
                        options[i] = selector.options[-1].text
                    selector.select_by_visible_text(options[i])
                    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'fa-spinner')))

                logging.debug("Running audit")
                mycuinfo.utils.find_id(driver, 'runAudit').click()
                WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'fa-spinner')))
                try:
                    driver.find_element_by_class_name('alert-warning')
                    logging.debug("Error message received - skipping")
                    driver.get('https://datc.prod.cu.edu/selfservice-cubld/audit/create.html')
                    mycuinfo.utils.find_link_text(driver, 'Select a Different Program:').click()
                    time.sleep(1)
                    mycuinfo.utils.find_id(driver, 'changeProgramButton').click()
                    time.sleep(1)
                    continue
                except NoSuchElementException:
                    pass

                college, degree, program, year = options
                save_dir = os.path.join(self.options.data_path, college, degree, year)
                save_filename = program + '.html'
                save_path = os.path.join(save_dir, save_filename)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                logging.debug("Saving file at %s" % save_path)
                try:
                    with open(save_path, 'w') as f:
                        f.write(driver.page_source)
                        f.close()
                except Exception as err:
                    driver.close()
                    raise err

                driver.get('https://datc.prod.cu.edu/selfservice-cubld/audit/create.html')

                mycuinfo.utils.find_link_text(driver, 'Select a Different Program:').click()
                time.sleep(1)
                mycuinfo.utils.find_id(driver, 'changeProgramButton').click()
                time.sleep(1)
            except queue.Empty:
                time.sleep(0.5)
            except KeyboardInterrupt as err:
                return
            except Exception as err:
                raise err
                logging.error("Error: %s" % err)
                self.program_queue.put(queue_head)
                self.program_queue.task_done()
                driver.close()
                driver = initDriver(self.username, self.password, self.options)

    def run(self):
        self.scrape()

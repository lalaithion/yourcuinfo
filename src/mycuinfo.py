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

def runSearch(driver):
	driver.find_element_by_link_text('Search for Classes').click()

	time.sleep(3)

	driver.switch_to_frame("ptifrmtgtframe")

	Select(driver.find_element_by_id("CLASS_SRCH_WRK2_INSTITUTION$31$")).select_by_value("CUBLD")
	time.sleep(1)
	Select(driver.find_element_by_id("CLASS_SRCH_WRK2_STRM$35$")).select_by_visible_text('Spring 2017 UC Boulder')
	time.sleep(1)
	Select(driver.find_element_by_id("SSR_CLSRCH_WRK_CAMPUS$0")).select_by_visible_text('Boulder Main Campus')
	time.sleep(1)
	driver.find_element_by_id("SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)
	time.sleep(1)
	driver.find_element_by_id("CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH").click()

def newDir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

url = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT"
ukeys = input("User: ").strip('\n')
pkeys = getpass.getpass()

loginTimer = 5 # time for login to complete
searchTimer = 10 # time for search to complete
minDropdownTimer = 3 # minimum time for dropdown to open
maxDropdownTimer = 15 # maximum time for dropdown to open

date = strftime("%Y-%m-%d", gmtime())
filepath = "../raw_html/" + date + "/"
newDir(filepath)
log = open(filepath + "log.txt", 'a+')
log.write("{0}\n{1}: Beggining new data harvest\n".format(date, strftime("%H:%M", gmtime())))
for current in departments_list.departments:
	try:
		driver = login(ukeys, pkeys)
	except Exception as err:
		log.write("Error logging in as {0}:\n  {1}\n".format(ukeys, err))
		driver.close()
		continue

	time.sleep(loginTimer)

	try:
		runSearch(driver)
	except Exception as err:
		log.write("Error getting to search for {0}:\n  {1}\n".format(current, err))
		driver.close()
		continue

	time.sleep(searchTimer)

	try:
		dropdownTimer = minDropdownTimer
		previousLenButtons = 0
		while True:
			time.sleep(dropdownTimer)
			buttons = driver.find_elements_by_class_name("PTEXPAND_ARROW")
			if len(buttons) == 0:
				break
			if len(buttons) == previousLenButtons:
				if dropdownTimer <= maxDropdownTimer:
					dropdownTimer += 1
				else:
					raise Exception("Unable to open dropdown")
			previousLenButtons = len(buttons)
			buttons[0].click()
	except Exception as err:
		log.write("Error during parsing of {0}:\n  {1}\n".format(current, err))
		driver.close()
		continue

	try:
		with open(filepath + current + ".html", 'w') as f:
			f.write(driver.page_source)
			f.close()
	except Exception as err:
		log.write("Error saving {0} to file:\n  {1}\n".format(current, err))

	driver.close()

log.write("{0}: Finished data harvest\n".format(strftime("%H:%M", gmtime())))
log.close()

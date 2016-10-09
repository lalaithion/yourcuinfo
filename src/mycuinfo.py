#!/usr/local/bin/python3

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import getpass
import time
from time import strftime, gmtime

import departments_list

mcui_login = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT"

ukeys = input("User: ").strip('\n')
pkeys = getpass.getpass()

for current in departments_list.departments:
    try:
        driver = webdriver.Firefox()
        driver.get(mcui_login)
        username = driver.find_element_by_id("username")
        username.clear()
        username.send_keys(ukeys)
        passwd = driver.find_element_by_id("password")
        passwd.clear()
        passwd.send_keys(pkeys)
        passwd.send_keys(Keys.RETURN)

        time.sleep(3)

        driver.find_element_by_link_text('Search for Classes').click()

        time.sleep(3)

        driver.switch_to_frame("ptifrmtgtframe")

        Select(driver.find_element_by_id("CLASS_SRCH_WRK2_INSTITUTION$31$")).select_by_value("CUBLD")
        time.sleep(1)
        Select(driver.find_element_by_id("CLASS_SRCH_WRK2_STRM$35$")).select_by_visible_text('Fall 2016 UC Boulder')
        time.sleep(1)
        Select(driver.find_element_by_id("SSR_CLSRCH_WRK_CAMPUS$0")).select_by_visible_text('Boulder Main Campus')
        time.sleep(1)
        driver.find_element_by_id("SSR_CLSRCH_WRK_SUBJECT$1").send_keys(current)
        time.sleep(1)
        driver.find_element_by_id("CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH").click()

        time.sleep(10)

        buttons = driver.find_elements_by_class_name("PTEXPAND_ARROW")
        while 1:
            time.sleep(3)
            buttons = driver.find_elements_by_class_name("PTEXPAND_ARROW")
            if len(buttons) == 0:
                break
            buttons[0].click()

        date = strftime("%Y-%m-%d", gmtime())
        with open("../raw_html/" + date + "-" + current + ".html",'w') as f:
            f.write(driver.page_source)

        driver.close()
    except Exception:
        driver.close()
        print(current + " Failed!")
        pass

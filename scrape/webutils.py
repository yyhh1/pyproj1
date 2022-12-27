import time
import random
import logging
from selenium import webdriver

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import winsound


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger()


def wait_until_elem_id_appear(driver, id_name, timeout=10):
    print("Waiting for id={}".format(id_name))
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.ID, id_name)))


def find_element_by_href_text(driver, href):
    return driver.find_element_by_xpath("//a[contains(@href, " + href + ")]")


def random_sleep_time(time_):
    return time_ + random.randint(-time_ * 5, time_ * 5) / 10


def random_sleep(time_):
    sleep_time = random_sleep_time(time_)
    time.sleep(sleep_time)


def open_chrome_with_url(url):
    browser = webdriver.Chrome()
    browser.get(url)

    return browser


def sound_finish(duration, freq=440):
    winsound.Beep(freq, duration*1000)

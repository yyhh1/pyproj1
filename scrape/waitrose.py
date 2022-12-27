from scrape.webutils import open_chrome_with_url, random_sleep, sound_finish
from selenium.webdriver.common.by import By
from datetime import datetime
import logging
import time

WURL = 'https://www.waitrose.com/ecom/login'
USERNAME = "hang.yuan@outlook.com"
PASSWORD = "heroes30"
CURL = 'https://www.waitrose.com/ecom/bookslot/delivery'


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger()


class WaitroseScraper:

    def __init__(self):
        self.open()

    def open(self):
        self.browser = open_chrome_with_url(WURL)
        random_sleep(2)
        continue_button = self.browser.find_element_by_xpath("//*[contains(text(), 'Yes, allow all')]")
        continue_button.click()
        time.sleep(2)

    def login(self):

        email_input = self.browser.find_element_by_id("email")
        email_input.send_keys(USERNAME)
        log.info('Email entered: {}'.format(USERNAME))
        random_sleep(2)

        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(PASSWORD)
        password_input.submit()
        random_sleep(5)
        log.info('Password entered: {}'.format('*'*len(PASSWORD)))

    def checkout(self):
        self.browser.get('https://www.waitrose.com/ecom/bookslot/delivery')

    def refresh(self):
        self.browser.refresh()
        time.sleep(5)

    def close(self):
        self.browser.close()

    def _parse_delivery_table(self):
        # self.refresh()
        tables = self.browser.find_elements(By.XPATH, '//table/tbody/tr')

        def parse_row(txt):
            splitted = txt.split('\n')
            if len(splitted) == 1:
                splitted = tables[0].text.split()
                res = [x + ' ' + y for x, y in zip(splitted[::2], splitted[1::2])]
                res = ['time'] + res
            else:
                res = splitted
            return res

        table_txt = [parse_row(table.text) for table in tables]
        table_txt = [x for x in table_txt if len(x) == 6]

        return table_txt

    def reopen(self):
        self.close()
        self.open()

    def parse_delivery_table(self):
        res = self._parse_delivery_table()
        if len(res) == 0:
            log.info('Parse failed. Try once again.')
            self.reopen()
            self.login()
            self.checkout()
            return self._parse_delivery_table()
        else:
            return res

    @staticmethod
    def find_available_slot(delivery):
        for i, date in enumerate(delivery[0][1:]):
            for j, time_ in enumerate([x[0] for x in delivery[1:]]):
                if delivery[j+1][i+1] not in ['Fully booked', 'Unavailable']:
                    return date + ' ' + time_
        return ''

    def find_slot(self):
        delivery = self.parse_delivery_table()
        slots = self.find_available_slot(delivery)

        if slots:
            log.info('Found available slot at {}. Please place asap.'.format(slots))
            return True
        else:
            log.info('No slot available.')
            return False

    def try_book_slot_until_success(self, timeout=60*60*12):
        start_time = datetime.now()
        while True:
            try:
                self.refresh()
                succeeded = self.find_slot()
                if succeeded:
                    log.info('Found a slot.')
                    sound_finish(5)
                    return True
                elapsed = datetime.now() - start_time
                if elapsed.seconds > timeout:
                    log.warning('We reach timeout {} without available slot. Exiting.'.format(timeout))
                    sound_finish(5)
                    return False
            except Exception as e:
                log.info('Request failed with exception {}. Continue.'.format(e))
                random_sleep(15)
                continue

            random_sleep(60)


if __name__ == "__main__":
    scraper = WaitroseScraper()
    scraper.login()
    scraper.checkout()
    scraper.try_book_slot_until_success()

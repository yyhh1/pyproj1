import logging
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from scrape.webutils import sound_finish, open_chrome_with_url, random_sleep, find_element_by_href_text

AMAZONURL = "https://primenow.amazon.co.uk/signin?returnUrl=https%3A%2F%2Fprimenow.amazon.co.uk%2Fhome"
CARTURL = "https://primenow.amazon.co.uk/cart"
USERNAME = "hang.yuan.47@gmail.com"
PASSWORD = "heroes30"

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger()


class AmazonPrime:

    def __init__(self):
        self.open()

    def open(self):
        self.browser = open_chrome_with_url(AMAZONURL)

    def login(self):
        email_input = self.browser.find_element_by_id("ap_email")
        email_input.send_keys(USERNAME)

        random_sleep(2)
        log.info('Email entered: {}'.format(USERNAME))

        password_input = self.browser.find_element_by_id("ap_password")
        password_input.send_keys(PASSWORD)
        # Wait for some time so it looks more like human
        random_sleep(2)
        password_input.submit()
        log.info('Password entered: {}'.format('*'*len(PASSWORD)))

    def close(self):
        self.browser.close()

    def to_cart(self):
        self.browser.get("https://primenow.amazon.co.uk/cart")

    def checkout(self):
        self.to_cart()
        checkout_button = find_element_by_href_text(self.browser, "'/checkout/enter-checkout'")
        checkout_button.click()

    def find_slot(self):

        no_slot_text = self.browser.find_elements_by_xpath(
            "//span[contains(text(), 'No delivery windows for today or tomorrow')]")

        if no_slot_text:
            return False
        try:
            am_slot = self.browser.find_element_by_xpath("//*[contains(text(), '00 AM']")
            am_slot.click()
            return True
        except NoSuchElementException:
            pass

        try:
            pm_slot = self.browser.find_element_by_xpath("//*[contains(text(), '00 PM']")
            pm_slot.click()
            return True
        except NoSuchElementException:
            pass

        return False

    def place_order(self):
        try:
            continue_button = self.browser.find_element_by_xpath("//*[contains(text(), 'Continue')]")
            continue_button.click()
        except NoSuchElementException:
            log.error("Could not find the 'Continue' button.")
            return False

        try:
            place_order_button = self.browser.find_element_by_xpath("//*[contains(text(), 'Place Your Order')]")
            place_order_button.click()
        except NoSuchElementException:
            log.error("Could not find the 'Place Your Order' button.")
            return False

        log.info('Order placed.')
        return True

    def find_and_book_slot(self):
        slot = self.find_slot()

        if not slot:
            log.info('No slot available.')
            return False
        else:
            log.info('Found available slot. Placing earliest possible.')
            self.place_order()

    def refresh(self):
        self.browser.refresh()
        random_sleep(5)

    def reopen(self):
        self.close()
        self.open()

    def try_book_slot_until_success(self, timeout=60*60*12):
        start_time = datetime.now()
        while True:
            try:
                self.refresh()
                succeeded = self.find_and_book_slot()
                if succeeded:
                    log.info('Booking complete. Should have a slot.')
                    sound_finish(5)
                    return True
            except Exception as e:
                log.info('Request failed with exception {}. Continue.'.format(e))
                self.reopen()
                self.login()
                self.checkout()

            elapsed = datetime.now() - start_time
            if elapsed.seconds > timeout:
                log.warning('We reach timeout {} without available slot. Exiting.'.format(timeout))
                sound_finish(5)
                return False

            random_sleep(55)


if __name__ == "__main__":
    amazon = AmazonPrime()
    amazon.login()
    amazon.checkout()
    res = amazon.try_book_slot_until_success()
    amazon.close()
    if res:
        log.info("This is the end of execution, we have slot booked.")
    else:
        log.info("This is the end of execution, but no slot booked.")

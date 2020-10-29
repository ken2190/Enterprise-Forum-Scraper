import re

from scrapy import Request
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from unicaps import CaptchaSolver, CaptchaSolvingService
from unicaps.exceptions import UnicapsException
from unicaps.common import CaptchaCharType, CaptchaAlphabet

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USERNAME = "thecreator"
PASSWORD = "Chq#Blast888"
KEY = "aiJZHkxlNhTiQA8orj8y"

PROXY_HOST = "127.0.0.1"
PROXY_PORT = "8118"
CAPTCHA_SOLVING_TRY_COUNT = 5


class CanadaHQSpider(MarketPlaceSpider):

    name = "canadahq_spider"

    # Url stuffs
    base_url = "https://canadahq.net/"
    login_url = "https://canadahq.net/login"
    home_url = "https://canadahq.net/home"

    # Css stuffs
    captcha_url_css = "div>img[src*=captcha]::attr(src)"

    # Xpath stuffs
    login_form_xpath= "//form[@method='post']"
    invalid_captcha_xpath = "//div[@class=\"alert alert-danger\"]/" \
                            "span/text()[contains(.,\"Invalid captcha\")]"
    market_url_xpath = '//div[@class="menu-content"]/ul/li/a/@href'
    product_url_xpath = '//a[@class="product"]/@href'
    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//a[contains(text(), "profile") and contains'\
                 '(text(), "View")]/@href'
    avatar_xpath = '//img[@class="img-responsive"]/@src'
    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def setup_browser(self, proxy_host=PROXY_HOST):
        # Init firefox options
        firefox_options = Options()
        firefox_options.headless = True

        firefox_profile = FirefoxProfile()

        # Set proxy
        firefox_profile.set_preference("network.proxy.type", 1)
        firefox_profile.set_preference("network.proxy.http", proxy_host)
        firefox_profile.set_preference("network.proxy.http_port", int(PROXY_PORT))
        firefox_profile.set_preference("network.proxy.ssl", proxy_host)
        firefox_profile.set_preference("network.proxy.ssl_port", int(PROXY_PORT))

        # Init web driver arguments
        webdriver_kwargs = {
            # "executable_path": "/usr/local/bin/geckodriver",
            "firefox_profile": firefox_profile,
            "options": firefox_options
        }

        # Load chrome driver
        return Firefox(**webdriver_kwargs)

    def log_in_using_browser(self):
        # helper functions
        def is_wrong_captcha(driver):
            return driver.find_elements_by_xpath(
                '//div[contains(@class, "alert-danger")]/span["Invalid captcha"]'
            )

        def is_logged_in(driver):
            return driver.find_elements_by_xpath('//a[contains(@href, "/logout")]')

        for _ in range(CAPTCHA_SOLVING_TRY_COUNT):
            # open base URL
            self.browser.get(self.base_url)

            # wait for Login button to load
            login_btn = WebDriverWait(self.browser, 30).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[text()="Login"]')
                )
            )

            # wait for CAPTCHA image to load
            captcha_img = self.browser.find_element_by_xpath(
                '//img[contains(@src, "/captcha/")]')
            WebDriverWait(self.browser, 30).until(
                lambda d: d.execute_script('return arguments[0].complete', captcha_img)
            )

            try:
                solved_captcha = self.solve_captcha(captcha_img.screenshot_as_png)
            except UnicapsException as exc:
                self.logger.error('Unable to solve CAPTCHA: %s', exc)
                raise

            captcha_text = str(solved_captcha.solution)
            if len(captcha_text) > 5:
                captcha_text = captcha_text.replace('l', '').replace('^', '').replace('|', '')

            self.logger.info(
                "Captcha has been solved: %s" % captcha_text
            )

            # input login data and submit
            self.browser.find_element_by_id('username').send_keys(USERNAME)
            self.browser.find_element_by_id('password').send_keys(PASSWORD)
            self.browser.find_element_by_name('captcha').send_keys(captcha_text)
            login_btn.click()

            try:
                login_result = WebDriverWait(self.browser, 60).until(
                    lambda d: is_wrong_captcha(d) or is_logged_in(d)
                )
            except TimeoutException:
                self.logger.error('Unable to log in the site (timeout)!')
                return

            if login_result[0].text == 'Invalid captcha':
                self.logger.warning('Invalid captcha, retrying...')
                solved_captcha.report_bad()
                continue

            solved_captcha.report_good()
            break

        if login_result[0].text == 'Invalid captcha':
            self.logger.error('Unable to solve the CAPTCHA (after %s tries)',
                              CAPTCHA_SOLVING_TRY_COUNT)
            return {}

        # get cookies
        bypass_cookies = {
            c.get("name"): c.get("value") for c in self.browser.get_cookies()
        }
        # set user-agent
        self.headers['User-Agent'] = self.browser.execute_script('return navigator.userAgent;')

        return bypass_cookies

    def solve_captcha(self, image_data):
        solver = CaptchaSolver(
            CaptchaSolvingService.ANTI_CAPTCHA,
            self.captcha_token
        )

        # solve image CAPTCHA
        return solver.solve_image_captcha(
            image=image_data,
            char_type=CaptchaCharType.ALPHANUMERIC,
            is_phrase=False,
            is_case_sensitive=False,
            is_math=False,
            alphabet=CaptchaAlphabet.LATIN,
            comment="Please ignore | and ^"
        )

    def start_requests(self):
        # init browser
        self.browser = self.setup_browser()

        try:
            # log in using browser and get cookies
            cookies = self.log_in_using_browser()
        finally:
            self.browser.quit()

        yield Request(
            url=self.home_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_start,
            cookies=cookies,
            meta={'proxy': f'http://{PROXY_HOST}:{PROXY_PORT}'}
        )


class CanadaHQScrapper(SiteMapScrapper):
    spider_class = CanadaHQSpider
    site_name = 'canadahq.at'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)

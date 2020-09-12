import os
import re
import logging
import time
# import dateparser

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Firefox,
    FirefoxProfile
)
from scraper.base_scrapper import (
    SeleniumSpider,
    SiteMapScrapper
)

# from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 1

CODE = 'skydiving'
USER = "moonbash"
PASS = '4KqPg@y.Ndn9bmeDeVRt_D*'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"

PROXY_HOST = "127.0.0.1"
PROXY_PORT = "8118"


class MazaSpider(SeleniumSpider):

    name = "maza_spider"
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "https://mfclubjof2s67ire.onion/"

    # Xpath stuffs
    forum_xpath = '//h2[@class="forumtitle"]/a/@href|'\
                  '//li[@class="subforum"]/a/@href'
    thread_xpath = '//ol[@id="threads"]/li[contains(@id,"thread_")]'
    thread_first_page_xpath = './/h3[@class="threadtitle"]'\
                              '/a[contains(@id, "thread_title_")]/@href'
    thread_last_page_xpath = './/dl[@class="pagination"]/dd/span[last()]'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '/@href'
    thread_date_xpath = './/em[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination_top"]'\
                        '//span[@class="selected"]/a/text()'
    post_date_xpath = '//span[@class="time"]/preceding-sibling::text()'
    avatar_xpath = '//a[@class="postuseravatar"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    handle_httpstatus_list = [400, 502]
    skip_forums = ['000']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        self.setup_browser()
        self.skip_forums = [f'f={i}' for i in self.skip_forums]

    def setup_browser(self, proxy_host=PROXY_HOST):

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger = logging.getLogger("selenium.webdriver")
        selenium_logger.setLevel(logging.ERROR)
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.ERROR)

        # Init firefox options
        firefox_options = Options()
        firefox_options.headless = True

        # Init firefox profile
        profile_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'firefox_profile'
        )
        firefox_profile = FirefoxProfile(profile_path)

        # Set proxy
        firefox_profile.set_preference("network.proxy.type", 1)
        firefox_profile.set_preference("network.proxy.http", proxy_host)
        firefox_profile.set_preference("network.proxy.http_port", int(PROXY_PORT))
        firefox_profile.set_preference("network.proxy.ssl", proxy_host)
        firefox_profile.set_preference("network.proxy.ssl_port", int(PROXY_PORT))

        # Init web driver arguments
        webdriver_kwargs = {
            "executable_path": "/usr/local/bin/geckodriver",
            "firefox_profile": firefox_profile,
            "options": firefox_options
        }

        # Load chrome driver
        self.browser = Firefox(**webdriver_kwargs)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            meta={
                "proxy": "http://%s:%s" % (PROXY_HOST, PROXY_PORT),
            }
        )

    def parse(self, response):

        if response.status != 400:
            self.browser.quit()
            self.setup_browser(proxy_host="tor")

        self.browser.get(self.base_url)
        time.sleep(self.delay)

        if self.browser.find_elements_by_xpath(
            '//i[text()="Вы забанены или используете старый сертификат."]'
        ):
            self.logger.error('User/cert is banned!')
            self.browser.quit()
            return

        # check for login form
        if self.browser.find_elements_by_name('vb_login_username'):
            self.log_in()

        # parse secret word
        if self.browser.find_elements_by_xpath('//td[contains(text(), "букву волшебного слова")]'):
            self.parse_code()

        # scrape forum
        self.parse_start()

    def log_in(self):
        userbox = self.browser.find_element_by_name('vb_login_username')
        passbox = self.browser.find_element_by_name('vb_login_password')
        checkbox = self.browser.find_element_by_name('cookieuser')
        userbox.send_keys(USER)
        passbox.send_keys(PASS)
        checkbox.click()
        passbox.submit()
        time.sleep(10)
        self.browser.get(self.base_url)
        time.sleep(self.delay)

        if not self.is_logged_in():
            self.logger.error('Failed to log in')

    def is_logged_in(self):
        return self.browser.find_elements_by_xpath('//a[text()="Log Out"]')

    def parse_code(self):
        response = fromstring(self.browser.page_source)
        code_block = response.xpath(
            '//td[contains(text(), "букву волшебного слова")]/text()')
        if not code_block:
            self.logger.info('Login Failed...Please try from browser')
            return
        self.logger.info('1st phase login successful. Entering code now..')
        code_block = code_block[0]
        self.logger.info(code_block)
        code_indexes = re.findall(r'введите (\d+) и (\d+) букву', code_block)
        code_indexes = code_indexes[0]
        code = ''
        for c in code_indexes:
            code += CODE[int(c) - 1]
        self.logger.info(f'Code to be entered is {code}')
        codebox = self.browser.find_element_by_name('subword')
        codebox.send_keys(code)
        submit = self.browser.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        time.sleep(10)
        self.logger.info('2nd phase login successful')


class MazaScrapper(SiteMapScrapper):
    spider_class = MazaSpider
    site_name = 'maza.la'

    def load_settings(self):
        settings = super().load_settings()
        return settings

import os
import re
import logging
import time
import dateparser

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Chrome,
    Firefox,
    FirefoxProfile
)
from scraper.base_scrapper import (
    SeleniumSpider,
    SiteMapScrapper
)

from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

CODE = 'ghostman'
USER = "gh0stpoodle"
PASS = 'xhuBLDwvTNn34PqS'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:76.0) '\
             'Gecko/20100101 Firefox/76.0'


class KorovkaSpider(SeleniumSpider):

    name = "maza_spider"

    # Url stuffs
    base_url = "https://korovka.cc/"
    login_url = "https://korovka.cc/login.php?do=login"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forumdisplay.php?f=")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = '//span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"]'\
                      '/a[contains(@name,"post")]/following-sibling::text()'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y, %H:%M'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger = logging.getLogger("selenium.webdriver")
        selenium_logger.setLevel(logging.ERROR)
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.ERROR)
        self.setup_browser()

    def setup_browser(self):

        # Init firefox options
        # firefox_options = Options()
        # firefox_options.headless = True

        # # Set proxy
        # firefox_profile.set_preference("network.proxy.type", 1)
        # firefox_profile.set_preference("network.proxy.http", PROXY_HOST)
        # firefox_profile.set_preference("network.proxy.http_port", PROXY_PORT)
        # firefox_profile.set_preference("network.proxy.ssl", PROXY_HOST)
        # firefox_profile.set_preference("network.proxy.ssl_port", PROXY_PORT)

        # Init web driver arguments
        # webdriver_kwargs = {
        #     "executable_path": "/usr/local/bin/geckodriver",
        #     "firefox_profile": firefox_profile,
        #     "options": firefox_options
        # }

        # Load chrome driver
        # self.browser = Firefox(**webdriver_kwargs)
        self.browser = Chrome()

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
        )

    def parse(self, response):
        self.browser.get(self.base_url)
        time.sleep(1)
        userbox = self.browser.find_element_by_name('vb_login_username')
        passbox = self.browser.find_element_by_name('vb_login_password')
        checkbox = self.browser.find_element_by_name('cookieuser')
        userbox.send_keys(USER)
        passbox.send_keys(PASS)
        checkbox.click()
        submit = self.browser.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        time.sleep(10)
        self.parse_code()

    def parse_code(self,):
        response = fromstring(self.browser.page_source)
        code_block = response.xpath(
            '//td[contains(text(), "буквы Вашего кодового слова форму")]'
            '/text()')
        if code_block:
            code_block = code_block[0]
            pattern = re.compile(r'Введите (\d+)-.*? и (\d+)')
        if not code_block:
            code_block = response.xpath(
                '//td[contains(text(), "Your code words in the form below")]'
                '/text()')
            if code_block:
                code_block = code_block[0]
                pattern = re.compile(r'Type (\d+)-.*? and (\d+)')
        if not code_block:
            self.parse_start()
        else:
            self.logger.info('1st phase login successful. Entering code now..')
            self.logger.info(code_block)
            code_indexes = pattern.findall(code_block)
            code_indexes = code_indexes[0]
            code = ''
            for c in code_indexes:
                code += CODE[int(c) - 1]
            time.sleep(3)
            self.logger.info(f'Code to be entered is {code}')
            codebox = self.browser.find_element_by_name('apa_authcode')
            codebox.send_keys(code)
            time.sleep(3)
            submit = self.browser.find_element_by_xpath(
                '//input[@type="submit"]')
            submit.submit()
            time.sleep(100)
            self.parse_start()


class KorovkaNewScrapper(SiteMapScrapper):

    spider_class = KorovkaSpider
    site_name = 'korovka.cc'

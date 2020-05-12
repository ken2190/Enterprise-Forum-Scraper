import os
import re
import logging
import time
import dateparser

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Chrome,
    ChromeOptions,
)
from scraper.base_scrapper import (
    SeleniumSpider,
    SiteMapScrapper
)

from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 2

CODE = 'ghostman'
USER = "gh0stpoodle"
PASS = 'xhuBLDwvTNn34PqS'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:76.0) '\
             'Gecko/20100101 Firefox/76.0'

PROXY = 'http://127.0.0.1:8118'


class KorovkaSpider(SeleniumSpider):

    name = "korovka_spider"
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "http://korovka32xc3t5cg.onion/"
    login_url = "http://korovka32xc3t5cg.onion/login.php?do=login"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forumdisplay.php?f=")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = './/span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"]'\
                      '/a[contains(@name,"post")]/following-sibling::text()'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]/img/@src'

    # Other settings
    use_proxy = False
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
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument('--proxy-server=%s' % PROXY)
        options.add_argument(f'user-agent={self.headers.get("User-Agent")}')
        self.browser = Chrome(options=options)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            meta={'proxy': PROXY}
        )

    def parse(self, response):
        self.browser.get(self.base_url)
        time.sleep(self.delay)
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
                code += CODE[int(c)-1]
            time.sleep(3)
            self.logger.info(f'Code to be entered is {code}')
            codebox = self.browser.find_element_by_name('apa_authcode')
            codebox.send_keys(code)
            time.sleep(3)
            submit = self.browser.find_element_by_xpath(
                '//form[contains(@action,"misc.php")]/input[@type="submit"]')
            submit.submit()
            time.sleep(5)
            self.parse_start()

    def parse_start(self, ):
        input_file = self.output_path + '/urls.txt'
        if os.path.exists(input_file):
            self.logger.info('URLs file found. Taking urls from this file')
            self.thread_last_page_xpath = None
            self.thread_pagination_xpath = '//a[@rel="next"]/@href'
            for thread_url in open(input_file, 'r'):
                thread_url = thread_url.strip()
                topic_id = self.topic_pattern.findall(thread_url)
                if not topic_id:
                    continue
                file_name = '{}/{}-1.html'.format(
                    self.output_path, topic_id[0])
                if os.path.exists(file_name):
                    continue
                self.parse_thread(thread_url, topic_id[0])
                time.sleep(self.delay)
            self.browser.quit()
        else:
            self.logger.info('URLs file not found. Performing normal scrape')
            super().parse_start()


class KorovkaNewScrapper(SiteMapScrapper):

    spider_class = KorovkaSpider
    site_name = 'korovka (korovka32xc3t5cg.onion)'

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


REQUEST_DELAY = 4

USERNAME = "xbyte"
PASSWORD = "Night#Byte001"

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:75.0) Gecko/20100101 Firefox/75.0"

PROXY = 'http://127.0.0.1:8118'


class VerifiedSpider(SeleniumSpider):

    name = 'verifiedsc_spider'
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "http://verified2ebdpvms.onion/"
    login_url = "http://verified2ebdpvms.onion/index.php"

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
    avatar_xpath = '//a[contains(@href, "member.php?")]/img/@src'

    # Other settings
    use_proxy = True
    handle_httpstatus_list = [504]
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y, %H:%M'
    stop_text = [
        'you have exceeded the limit of page views in 24 hours',
        'you have reached the limit of viewing topics per day.'
    ]

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
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--proxy-server=%s' % PROXY)
        chrome_options.add_argument(f'user-agent={self.headers.get("User-Agent")}')
        self.browser = Chrome(
            '/usr/local/bin/chromedriver',
            chrome_options=chrome_options)

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            dont_filter=True,
            meta={'proxy': PROXY}
        )

    def parse(self, response):
        self.browser.get(self.login_url)
        time.sleep(self.delay)
        userbox = self.browser.find_element_by_name('vb_login_username')
        passbox = self.browser.find_element_by_name('vb_login_password')
        checkbox = self.browser.find_element_by_name('cookieuser')
        userbox.send_keys(USERNAME)
        passbox.send_keys(PASSWORD)
        checkbox.click()
        submit = self.browser.find_element_by_xpath('//button[@type="submit"]')
        submit.click()
        time.sleep(10)
        self.parse_code()

    def parse_code(self,):
        response = fromstring(self.browser.page_source)
        code_number = response.xpath(
            '//div[@class="personalCodeBrown"]/font/text()')
        code_value = self.backup_codes[int(code_number[0])-1]\
            if code_number else None
        if not code_value:
            self.parse_start()
        else:
            self.logger.info('1st phase login successful. Entering code now..')
            self.logger.info(f'Code no: {code_number[0]}; Code Value: {code_value}')
            time.sleep(3)
            codebox = self.browser.find_element_by_name('code')
            codebox.send_keys(code_value)
            time.sleep(3)
            submit = self.browser.find_element_by_xpath(
                '//form[@id="codeEnterForm"]/button[@type="submit"]')
            submit.submit()
            time.sleep(10)
            self.parse_start()
        self.browser.quit()

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


class VerifiedScrapper(SiteMapScrapper):

    spider_class = VerifiedSpider
    site_name = 'verified (verified2ebdpvms.onion)'
    site_type = 'forum'

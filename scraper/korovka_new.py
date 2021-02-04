import os
import csv
import re
import logging
import time
import dateparser
from itertools import cycle

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

# Delay between each request
REQUEST_DELAY = 5

# No of pages to be scraped from single account
SCRAPE_PER_ACCOUNT = 20

# Wait time(minutes) to login another account once scrape limit is reached
ACCOUNT_DELAY = 30


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

PROXY = 'http://127.0.0.1:8118'


class KorovkaSpider(SeleniumSpider):

    name = "korovka_spider"
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "https://korovka.cc/"
    login_url = "https://korovka.cc/login.php?do=login"

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
    use_proxy = "On"
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y, %H:%M'
    ban_text = 'date the ban'
    current_scrape_count = 0

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
        self.read_urls()
        self.read_credentials()

    def setup_browser(self):
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument('--proxy-server=%s' % PROXY)
        options.add_argument(f'user-agent={self.headers.get("User-Agent")}')
        self.browser = Chrome(options=options)

    def read_urls(self):
        urls = set()
        input_file = self.output_path + '/urls.txt'
        if not os.path.exists(input_file):
            self.url_iterator = None
            return
        self.thread_last_page_xpath = None
        self.thread_pagination_xpath = '//a[@rel="next"]/@href'
        with open(input_file, 'r') as fp:
            urls = [url.strip() for url in fp.readlines()]
        self.url_iterator = iter(urls)

    def read_credentials(self,):
        self.credentials = list()
        with open('credentials/korovka_accounts.csv') as fp:
            reader = csv.reader(fp)
            for index, row in enumerate(reader):
                if index == 0:
                    continue
                self.credentials.append([row[6], row[4], row[7]])
        self.credentials_iterator = cycle(self.credentials)

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            meta={'proxy': PROXY}
        )

    def parse(self, response):
        credentials = next(self.credentials_iterator)
        self.logger.info(f"Proceeding login for {credentials[0]}")
        self.proceed_for_login(credentials)
        time.sleep(5)
        self.parse_start()

    def proceed_for_login(self, credentials):
        self.browser.get(self.base_url)
        time.sleep(self.delay)
        userbox = self.browser.find_element_by_name('vb_login_username')
        passbox = self.browser.find_element_by_name('vb_login_password')
        checkbox = self.browser.find_element_by_name('cookieuser')
        userbox.send_keys(credentials[0])
        passbox.send_keys(credentials[1])
        checkbox.click()
        submit = self.browser.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        time.sleep(10)
        self.parse_code(credentials[2])

    def parse_code(self, code_string):
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
            self.logger.info('Invalid credentials. Trying with next user')
            self.next_user_login()
            return
        self.logger.info('1st phase login successful. Entering code now..')
        self.logger.info(code_block)
        code_indexes = pattern.findall(code_block)
        code_indexes = code_indexes[0]
        code = ''
        for c in code_indexes:
            code += code_string[int(c)-1]
        time.sleep(3)
        self.logger.info(f'Code to be entered is {code}')
        codebox = self.browser.find_element_by_name('apa_authcode')
        codebox.send_keys(code)
        time.sleep(3)
        submit = self.browser.find_element_by_xpath(
            '//form[contains(@action,"misc.php")]/input[@type="submit"]')
        submit.submit()

    def get_next_url_and_topic_id(self, ):
        try:
            thread_url = next(self.url_iterator)
            self.logger.info(f'Proceeding for url: {thread_url}')
        except StopIteration:
            return None, None
        topic_id = self.topic_pattern.findall(thread_url)
        if not topic_id:
            return self.get_next_url_and_topic_id()
        return thread_url, topic_id[0]

    def parse_start(self, ):
        if self.ban_text in self.browser.page_source.lower():
            self.logger.info('User banned. Trying with next user')
            self.next_user_login()
        if self.url_iterator:
            thread_url, topic_id = self.get_next_url_and_topic_id()
            self.parse_thread(thread_url, topic_id)
        else:
            response = fromstring(self.browser.page_source)
            all_forums = response.xpath(self.forum_xpath)
            for forum_url in all_forums:

                # Standardize url
                if self.base_url not in forum_url:
                    forum_url = self.base_url + forum_url
                self.process_forum(forum_url)
                time.sleep(self.delay)

    def process_forum(self, forum_url):
        self.browser.get(forum_url)
        response = fromstring(self.browser.page_source)
        if self.ban_text in self.browser.page_source.lower():
            self.logger.info('User banned. Trying with next user')
            self.next_user_login()
            self.browser.get(forum_url)
        self.logger.info(f"Next_page_url: {forum_url}")
        threads = response.xpath(self.thread_xpath)
        lastmod_pool = []
        for thread in threads:
            thread_url, thread_lastmod = self.extract_thread_stats(thread)
            if not thread_url:
                continue

            if self.start_date and thread_lastmod is None:
                self.logger.info(
                    "Thread %s has no last update in update scraping, "
                    "so ignored." % thread_url
                )
                continue

            lastmod_pool.append(thread_lastmod)

            # If start date, check last mod
            if self.start_date and thread_lastmod < self.start_date:
                self.logger.info(
                    "Thread %s last updated is %s before start date %s. "
                    "Ignored." % (thread_url, thread_lastmod, self.start_date)
                )
                continue

            # Standardize thread url
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url

            # Parse topic id
            try:
                topic_id = self.topic_pattern.findall(thread_url)[0]
            except Exception:
                continue

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                continue

            self.parse_thread(thread_url, topic_id)

        # Pagination
        if not lastmod_pool:
            self.logger.info(
                "Forum without thread, exit."
            )
            return

        if self.start_date and self.start_date > max(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. "
                "Exit." % (self.start_date, forum_url)
            )
            return
        next_page = self.get_forum_next_page(response)
        if next_page:
            self.process_forum(next_page)

    def parse_thread(self, thread_url, topic_id):
        self.browser.get(thread_url)
        response = fromstring(self.browser.page_source)
        if self.ban_text in self.browser.page_source.lower():
            self.logger.info('User banned. Trying with next user')
            self.next_user_login()
            self.browser.get(thread_url)
        post_dates = [
            dateparser.parse(post_date.strip()) for post_date in
            response.xpath(self.post_date_xpath)
            if post_date.strip() and dateparser.parse(post_date.strip())
        ]
        if self.start_date and max(post_dates) < self.start_date:
            self.logger.info(
                "No more post to update."
            )
            return

        current_page = self.get_thread_current_page(response)
        with open(
            file=os.path.join(
                self.output_path,
                "%s-%s.html" % (topic_id, current_page)
            ),
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(self.browser.page_source)
            self.logger.info(
                f'{topic_id}-{current_page} done..!'
            )
            self.topic_pages_saved += 1

            # Update stats
            self.crawler.stats.set_value(
                "topic pages saved",
                self.topic_pages_saved
            )

            # Kill task if kill count met
            if self.kill and self.topic_pages_saved >= self.kill:
                raise CloseSpider(reason="Kill count met, shut down.")
        time.sleep(self.delay)
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.parse_thread(next_page, topic_id)
        else:
            self.current_scrape_count += 1
            self.check_scrape_status()

    def check_scrape_status(self):
        if self.current_scrape_count < SCRAPE_PER_ACCOUNT:
            if self.url_iterator:
                thread_url, topic_id = self.get_next_url_and_topic_id()
                if not thread_url:
                    self.browser.quit()
                    return
                self.parse_thread(thread_url, topic_id)
        else:
            self.logger.info(
                "Maximum scraped limit for this user. "
                f"Waiting {ACCOUNT_DELAY} minutes to login next account"
            )
            time.sleep(ACCOUNT_DELAY*60)
            self.current_scrape_count = 0
            self.next_user_login()

    def next_user_login(self):
        self.browser.quit()
        self.setup_browser()
        credentials = next(self.credentials_iterator)
        self.logger.info(f"Proceeding login for {credentials[0]}")
        self.proceed_for_login(credentials)
        time.sleep(5)


class KorovkaNewScrapper(SiteMapScrapper):

    spider_class = KorovkaSpider
    site_name = 'korovka (korovka32xc3t5cg.onion)'
    site_type = 'forum'

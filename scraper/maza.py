import os
import re
import logging
import time
import dateparser

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Firefox,
    FirefoxProfile
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

CODE = 'shithead'
USER = "Sandman"
PASS = 'Night#MF_0010'

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) "\
             "Gecko/20100101 Firefox/75.0"

PROXY_HOST = "127.0.0.1"
PROXY_PORT = "8118"


class MazaSpider(SitemapSpider):

    name = "maza_spider"

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
    thread_date_xpath = '//em[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination_top"]'\
                        '//span[@class="selected"]/a/text()'
    post_date_xpath = '//span[@class="time"]/preceding-sibling::text()'
    avatar_xpath = '//a[@class="postuseravatar"]/img/@src'

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

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
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    handle_httpstatus_list = [400]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        self.setup_browser()

    def setup_browser(self):

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)
        selenium_logger = logging.getLogger("selenium.webdriver")
        selenium_logger.setLevel(logging.ERROR)
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.ERROR)

        # Init firefox options
        firefox_options = Options()
        firefox_options.headless = False

        # Init firefox profile
        profile_path = os.path.dirname(os.path.abspath(__file__)).replace(
            '/scraper', '/firefox_profile')
        firefox_profile = FirefoxProfile(profile_path)

        # Set proxy
        firefox_profile.set_preference("network.proxy.type", 1)
        firefox_profile.set_preference("network.proxy.http", PROXY_HOST)
        firefox_profile.set_preference("network.proxy.http_port", PROXY_PORT)
        firefox_profile.set_preference("network.proxy.ssl", PROXY_HOST)
        firefox_profile.set_preference("network.proxy.ssl_port", PROXY_PORT)

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
        self.parse_start()

    def parse_start(self):
        response = fromstring(self.browser.page_source)
        all_forums = response.xpath(self.forum_xpath)
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # self.logger.info(forum_url)
            self.process_forum(forum_url)

        self.browser.quit()

    def process_forum(self, forum_url):
        self.browser.get(forum_url)
        response = fromstring(self.browser.page_source)
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

    def extract_thread_stats(self, thread):

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = thread.xpath(
                self.thread_first_page_xpath
            )

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            )

        thread_lastmod = thread.xpath(
            self.thread_date_xpath
        )

        # Process stats
        if thread_last_page_url:
            thread_url = thread_last_page_url[0]
        elif thread_first_page_url:
            thread_url = thread_first_page_url[0]
        else:
            thread_url = None

        try:
            thread_lastmod = dateparser.parse(thread_lastmod[0].strip())
        except Exception as err:
            thread_lastmod = None

        return thread_url, thread_lastmod

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath)
        if not next_page:
            return
        next_page = next_page[0].strip()
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def parse_thread(self, thread_url, topic_id):
        self.browser.get(thread_url)
        response = fromstring(self.browser.page_source)
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
        self.parse_avatars(response)
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.parse_thread(next_page, topic_id)

    def get_thread_current_page(self, response):
        current_page = response.xpath(self.thread_page_xpath)
        return current_page[0] if current_page else '1'

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.thread_pagination_xpath)
        if not next_page:
            return
        next_page = next_page[0].strip()
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def parse_avatars(self, response):

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath)
        for avatar_url in all_avatars:

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            try:
                file_name = os.path.join(
                    self.avatar_path,
                    f'{self.avatar_name_pattern.findall(avatar_url)[0]}.png'
                )
            except Exception:
                continue

            if os.path.exists(file_name):
                continue

            self.save_avatar(avatar_url, file_name)

    def save_avatar(self, avatar_url, file_name):
        self.browser.get(avatar_url)
        avatar_name = os.path.basename(file_name)
        with open(file_name, 'wb') as file:
            file.write(
                self.browser.find_element_by_xpath(
                    '//img').screenshot_as_png
            )
        self.logger.info(f"Avatar {avatar_name} done..!")


class MazaScrapper(SiteMapScrapper):
    spider_class = MazaSpider
    site_name = 'maza'

    def load_settings(self):
        settings = super().load_settings()
        return settings

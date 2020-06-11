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
    SeleniumSpider,
    SiteMapScrapper
)

from scrapy.exceptions import CloseSpider

from lxml.html import fromstring


REQUEST_DELAY = 1.5

CODE = 'shithead'
USER = "Sandman"
PASS = 'Night#MF_0010'

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:75.0) Gecko/20100101 Firefox/75.0"

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
    handle_httpstatus_list = [400]
    skip_forums = [204, 194, 208, 221, 153, 171, 168, 203, 191, 192, 169, 211, 102, 28, 155, 162, 150, 224, 155, 84, 187, 90, 188, 196, 197, 47, 83, 189, 149, 121, 184, 112, 122, 186, 205, 114, 40, 76, 185, 219, 201, 206, 120, 217, 128, 111, 127, 170, 119, 181, 216, 82, 113, 118, 180, 182, 169, 198, 199, 110, 179, 65, 43, 44, 73, 178, 215, 100, 177, 202, 176, 214, 72, 42, 70, 146, 49, 78, 175, 173, 117, 174, 109, 213, 46, 159, 195, 210, 48, 190, 154, 64, 207, 218, 38, 223, 160, 193]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        self.setup_browser()
        self.skip_forums = [f'f={i}' for i in self.skip_forums]

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
        firefox_options.headless = True

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


class MazaScrapper(SiteMapScrapper):
    spider_class = MazaSpider
    site_name = 'maza.la'

    def load_settings(self):
        settings = super().load_settings()
        return settings

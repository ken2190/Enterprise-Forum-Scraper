import base64
import io
import logging
import time

import imagehash
from PIL import Image
from scrapy import Request
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import (
    Firefox,
    FirefoxProfile
)
from scraper.base_scrapper import (
    SeleniumSpider,
    SiteMapScrapper
)

REQUEST_DELAY = 2

USER = 'Cyrax_011'
PASS = 'Night#India065'

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:75.0) Gecko/20100101 Firefox/75.0"

PROXY_HOST = "127.0.0.1"
PROXY_PORT = "8118"


class EnvoySpider(SeleniumSpider):
    name = 'envoy_spider'
    delay = REQUEST_DELAY

    # Url stuffs
    base_url = "http://envoys5appps3bin.onion/"

    # Xpath stuffs
    forum_xpath = ''
    thread_xpath = ''
    thread_first_page_xpath = ''
    thread_last_page_xpath = ''
    thread_date_xpath = ''

    pagination_xpath = ''
    thread_pagination_xpath = ''
    thread_page_xpath = ''
    post_date_xpath = ''
    avatar_xpath = ''

    # Other settings
    use_proxy = False
    handle_httpstatus_list = [502, 503]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )
        self.setup_browser()

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

        firefox_profile = FirefoxProfile()

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

        self.browser.get(self.base_url)
        time.sleep(10)

        while True:
            if not self.browser.find_elements_by_css_selector('form.captcha_form'):
                break

            self.logger.info('Trying to bypass Envoy X-Ray Anti-DDOS protection...')
            self.bypass_anti_ddos(response)

        self.logger.info('Envoy X-Ray Anti-DDOS protection was bypassed successfully!')

        if self.browser.current_url.endswith('/page/soon'):
            msg = self.browser.find_element_by_css_selector('.soon-content').text
            self.logger.info(msg)
            return

    def bypass_anti_ddos(self, response):
        spans = self.browser.find_elements_by_css_selector('form.captcha_form span.c')
        img_srcs = [
            s.find_element_by_xpath('label/img').get_attribute('src').split(',')[1]
            for s in spans
        ]
        imgs = [Image.open(io.BytesIO(base64.b64decode(i))) for i in img_srcs]

        res_indexes = []
        get_diff = lambda i1, i2: imagehash.average_hash(i1) - imagehash.average_hash(i2)
        for n in range(len(imgs)):
            min_diff = None
            for i in range(len(imgs)):
                if n == i:
                    continue
                diff = get_diff(imgs[n], imgs[i])
                if min_diff is None or diff < min_diff:
                    min_diff = diff

            res_indexes.append(min_diff)

        if res_indexes:
            img_index = res_indexes.index(max(res_indexes))

            checkbox = spans[img_index].find_element_by_tag_name('input')
            checkbox.click()
            checkbox.submit()
        else:
            self.browser.refresh()

        time.sleep(10)


class EnvoyScrapper(SiteMapScrapper):
    spider_class = EnvoySpider
    site_name = 'envoy_envoys5appps3bin'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings

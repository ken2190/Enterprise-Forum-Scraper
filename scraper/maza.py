import re
import logging
import time

from selenium.webdriver.firefox.options import Options
from scrapy import Request
from selenium.webdriver import (
    Firefox,
    FirefoxProfile
)
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"

PROXY_HOST = "127.0.0.1"
PROXY_PORT = "8118"


class MazaSpider(MarketPlaceSpider):

    name = "maza_spider"

    # Url stuffs
    base_url = "https://mfclubjof2s67ire.onion"

    # xpath stuffs
    login_form_xpath = captcha_form_xpath = '//form[@method="post"]'
    captcha_url_xpath = '//img[@name="capt_code"]/@src'
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
    handle_httpstatus_list = [400]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = super().synchronize_meta(response, default_meta)
        meta.update({'proxy': PROXY})
        return meta

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
        self.load_cert()
        return

    def load_cert(self):

        # Init logger
        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)

        # Init firefox options
        firefox_options = Options()
        firefox_options.headless = False

        # Init firefox profile
        firefox_profile = FirefoxProfile("/home/osboxes/Desktop/factory/forumparser/firefox_profile")

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
        browser = Firefox(**webdriver_kwargs)

        browser.get(self.base_url)

        time.sleep(360)

        browser.quit()


class MazaScrapper(SiteMapScrapper):
    spider_class = MazaSpider
    site_name = 'maza'

    def load_settings(self):
        settings = super().load_settings()
        return settings

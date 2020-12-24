import re

from scrapy import (
    Request,
    FormRequest
)
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

USERNAME = "thecreator"
PASSWORD = "Chq#Blast888"
KEY = "aiJZHkxlNhTiQA8orj8y"

PROXY = 'http://127.0.0.1:8118'
CAPTCHA_SOLVING_TRY_COUNT = 5


class CanadaHQSpider(MarketPlaceSpider):

    name = "canadahq_spider"

    # Url stuffs
    base_url = "https://canadahq.net/"
    login_url = "https://canadahq.net/login"
    home_url = "https://canadahq.net/home"

    # Css stuffs
    captcha_url_xpath = "//img[contains(@src, 'captcha')]/@src"
    captcha_token_xpath = "//input[@name='_token']/@value"

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

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            dont_filter=True,
            meta={
                'proxy': PROXY,
            }
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load cookies

        cookies = response.request.headers.get("Cookie")
        if not cookies:
            yield from self.start_requests()
            return

        # Load captcha url
        captcha_url = response.xpath(
                self.captcha_url_xpath).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )
        
        captcha_token = response.xpath(self.captcha_token_xpath).extract_first()
        formdata = {
            "_token": captcha_token,
            "captcha": captcha,
            "username": USERNAME,
            "password": PASSWORD,
        }

        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.parse_start
        )
    
    def parse_start(self, response):

        if response.xpath(self.captcha_token_xpath).extract_first():
            yield Request(
                url=self.login_url,
                headers=self.headers,
                callback=self.parse_login,
                dont_filter=True,
                meta=self.synchronize_meta(response)
            )
        else:
            yield from super().parse_start(response)

class CanadaHQScrapper(SiteMapScrapper):
    spider_class = CanadaHQSpider
    site_name = 'canadahq.at'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)

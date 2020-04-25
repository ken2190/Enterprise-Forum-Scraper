import os
import re
import uuid

from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
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

PROXY = 'http://127.0.0.1:8118'


class ApollonSpider(MarketPlaceSpider):

    name = "apollon_spider"

    # Url stuffs
    base_url = "http://apollionih4ocqyd.onion/"
    login_url = "http://apollionih4ocqyd.onion/login.php"

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
    # Other settings
    # custom_settings = {
    #     "DOWNLOADER_MIDDLEWARES": {
    #         'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700
    #     }
    # }
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    captcha_instruction = "Please ignore | and ^"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

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
        cookies = response.request.headers.get("Cookie").decode("utf-8")
        if not cookies:
            yield from self.start_requests()
            return
        # Load captcha url
        captcha_url = f'{self.base_url}cap/capshow.php'
        captcha = self.solve_captcha(
            captcha_url,
            response,
            headers={
                "Referer": "http://apollionih4ocqyd.onion/login.php",
                "Host": "apollionih4ocqyd.onion"
            }
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            'I_username': USERNAME,
            'I_password': PASSWORD,
            "capt_code": captcha
        }

        yield FormRequest(
            self.login_url,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        self.logger.info(response.text)
        return

        # Check valid captcha
        is_invalid_captcha = response.xpath(
            self.invalid_captcha_xpath).extract_first()
        if is_invalid_captcha:
            self.logger.info(
                "Invalid captcha."
            )
            return

        yield from super().parse_start(response)


class ApollonScrapper(SiteMapScrapper):
    spider_class = ApollonSpider
    site_name = 'apollon (apollionih4ocqyd.onion)'

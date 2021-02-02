import os
import re
import uuid
import base64
import time

from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)

USERNAME='gordal418'
PASSWORD="readytogo418"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

PROXY = 'http://127.0.0.1:8118'


class TheVersusSpider(MarketPlaceSpider):

    name = "theversus_spider"

    # Url stuffs
    base_url = "http://pqqmr3p3tppwqvvapi6fa7jowrehgd36ct6lzr26qqormaqvh6gt4jyd.onion"

    # xpath stuffs
    login_form_xpath = '//form[contains(@action, "/login")]'
    captch_form_xpath = '//form[@method="post"]'
    captcha_url_xpath = '//img[contains(@src, "/captcha")]/@src'
    captchaData_xpath = '//input[@name="captcha"]/@value'
    login_csrf_xpath = '//input[@name="CSRF"]/@value'

    market_url_xpath = '//ul//a[@href="/listing"]/@href'
    product_url_xpath = '//div[contains(@class, "listings__product")]//a[contains(@href, "/listing/")]/@href'

    next_page_xpath = '//div[@class="pagination__navigation"]/a[normalize-space(text())=">"]/@href'

    user_xpath = '//div[contains(@class, "listing__vendor")]//a[contains(@href, "/user/")]/@href'
    user_description_xpath = '//div[contains(@class, "user__navigation")]//a[contains(@href, "/feedbacks")]/@href'
    user_pgp_xpath = '//div[contains(@class, "user__navigation")]//a[contains(@href, "/pgp")]/@href'
    avatar_xpath = '//img[contains(@class, "listing__gallery-img")]/@src'

    # Login Failed Message xpath
    login_failed_xpath = '//*[contains(., "Username or password wrong!")]'
    captcha_failed_xpath = '//div[contains(@class, "alert alert-danger") and contains(., "The Captcha code")]'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700
        }
    }
    use_proxy = "Tor"

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
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_captcha,
            errback=self.check_site_error,
            dont_filter=True,
            meta={
                'proxy': PROXY,
                'handle_httpstatus_list': [302]
            }
        )

    def parse_captcha(self, response):

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

        captchaData = response.xpath(self.captchaData_xpath).extract_first()
        formdata = {
            "solution": captcha,
            "captcha": captchaData
        }
        yield FormRequest.from_response(
            response=response,
            formxpath=self.captch_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_login,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Check if bypass captcha failed
        self.check_if_captcha_failed(response, self.captcha_url_xpath)

        # Load cookies
        cookies = response.request.headers.get("Cookie")
        if not cookies:
            yield from self.start_requests()
            return

        CSRF = response.xpath(self.login_csrf_xpath).extract_first()
        
        formdata = {
            "Username": USERNAME,
            "Password": PASSWORD,
            "CSRF:": CSRF
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

        # Check if login failed
        self.check_if_logged_in(response)

        yield from super().parse_start(response)


class TheVersusScrapper(SiteMapScrapper):
    spider_class = TheVersusSpider
    site_name = 'TheVersus'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


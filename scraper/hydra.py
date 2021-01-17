import os
import re
import uuid
import base64

from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    MarketPlaceSpider,
    SiteMapScrapper
)


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

USERNAME = "gordon415"
PASSWORD = "readytogo418"

PROXY = 'http://127.0.0.1:8118'


class HydraSpider(MarketPlaceSpider):

    name = "hydramarket_spider"

    # Url stuffs
    base_url = "http://hydraruzxpnew4af.onion"

    # xpath stuffs
    login_form_xpath = '//form[contains(@action, "/login")]'
    captch_form_xpath = '//form[@method="post"]'
    captcha_url_xpath = '//img[@alt="Captcha image"]/@src'
    captchaData_xpath = '//input[@name="captchaData"]/@value'
    market_url_xpath = '//div/a[@role and contains(@href, "/market/")]/@href'
    product_url_xpath = '//div[@class="title over"]/a[contains(@href, "/product/")]/@href'
    next_page_xpath = '//ul[@class="pagination"]/li[@class="pag_right"]/a/@href'

    avatar_xpath = '//div[@class="product_img_big"]//img/@src'

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
    use_proxy = "On"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def get_captcha_image_content(self, image_url, cookies={}, headers={}, proxy=None):

        # Separate the metadata from the image data
        head, data = image_url.split(',', 1)

        # Decode the image data
        plain_data = base64.b64decode(data)

        return plain_data

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

        formdata = {
            "captcha": captcha
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
            "_token":"",
            "redirect": "1",
            "captcha": captcha,
            "login": USERNAME,
            "password": PASSWORD,
            "captchaData:": captchaData
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

        if response.xpath(self.captcha_url_xpath):
            self.logger.info("Invalid Captcha")
            return
        yield from super().parse_start(response)


class HydraScrapper(SiteMapScrapper):
    spider_class = HydraSpider
    site_name = 'hydra_hydraruzxpnew4af'
    site_type = 'marketplace'

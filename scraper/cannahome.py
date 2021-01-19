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


class CannaHomeSpider(MarketPlaceSpider):

    name = "cannahome_spider"

    # Url stuffs
    base_url = "http://cannabmgae3mkekotfzsyrx5lqg7lj7hgcn6t4rumqqs5vnvmuzsmfqd.onion"

    # xpath stuffs
    login_form_xpath = '//form[@id="login-form"]'

    market_url_xpath = '//div[contains(@class, "dropdown")]/a[contains(@href, "/listings/")]/@href'
    product_url_xpath = '//div[@class="listing"]//a[contains(@class, "name")]/@href'

    next_page_xpath = '//div[contains(@class, "row panel")]//a[contains(@class, "btn arrow-right")]/@href'

    user_xpath = '//section[@id="main"]//div[contains(@class, "rows-20")]//a[contains(@href, "/v/")]/@href'
    avatar_xpath = '//div[contains(@class, "product")]//a[contains(@href, "/upload/")]/@href'

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
    use_proxy = False

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

        # Load captcha url
        captcha_url = self.base_url + "/captcha"
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )
        
        formdata = {
            "username": USERNAME,
            "password": PASSWORD,
            "captcha": captcha
        }
        print(formdata)
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

        if response.xpath(self.login_form_xpath):
            self.logger.info("Invalid Captcha or Invalid Login")
            return
        yield from super().parse_start(response)


class CannaHomeScrapper(SiteMapScrapper):
    spider_class = CannaHomeSpider
    site_name = 'CannaHome'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


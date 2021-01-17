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

USERNAME='gordal418'
PASSWORD='readytogo418'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

PROXY = 'http://127.0.0.1:8118'


class TorrezSpider(MarketPlaceSpider):

    name = "torrez_spider"

    # Url stuffs
    base_url = "http://333f7gpuishjximodvynnoisxujicgwaetzywgkxoxuje5ph3qyqjuid.onion/"

    # xpath stuffs
    captch_form_xpath = '//form[@method="POST"]'
    captcha_url_xpath_1 = '//div[contains(@class, "login")]//img/@src'
    captcha_id_xpath = '//input[@name="captcha_id"]/@value'
    captcha_try = 5

    login_form_xpath = '//form[contains(@action, "/login")]'
    captcha_url_xpath_2 = '//form//img/@src'
    captcha_token_xpath = '//input[@name="_token"]/@value'

    market_url_xpath = '//ul[@class="sidebar"]/li[@class="position-relative"]/a/@href'
    product_url_xpath = '//table[contains(@class, "table-listings")]//td[contains(@class, "maxThumb")]/a/@href'

    next_page_xpath = '//ul[contains(@class, "pagination")]//a[@rel="next"]/@href'
    user_xpath = '//div[contains(@class, "singleItemDetails")]//a[contains(@href, "/profile/")]/@href'
    user_pgp_xpath = '//li[contains(@class, "nav-item")]/a[contains(@href, "/pgp")]/@href'
    avatar_xpath = '//div[contains(@class, "thumbnail singleItem")]//img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

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
            callback=self.parse_captcha_1,
            dont_filter=True,
            meta={
                'proxy': PROXY,
            }
        )

    def get_product_next_page(self, response):
        next_page_url = response.xpath(self.next_page_xpath).extract_first()
        if not next_page_url:
            return
        if self.base_url not in next_page_url:
            next_page_url = self.base_url + next_page_url
        return next_page_url


    def parse_captcha_1(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load cookies
        cookies = response.request.headers.get("Cookie")
        if not cookies:
            yield from self.start_requests()
            return

        # Load captcha url
        captcha_url = response.xpath(
                self.captcha_url_xpath_1).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        captcha_id = response.xpath(self.captcha_id_xpath).extract_first()
        formdata = {
            "captcha": captcha,
            "captcha_id": captcha_id
        }
        self.logger.debug(f'Form data: {formdata}')

        yield FormRequest.from_response(
            response=response,
            formxpath=self.captch_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_captcha_2,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_captcha_2(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        if response.xpath(self.captcha_url_xpath_1):
            self.captcha_try = self.captcha_try - 1
            if not self.captcha_try:
                self.logger.info("Invalid Captcha")
                return
            else:   
                self.logger.info("Invalid Captcha, Try again")
                yield Request(
                    url=self.base_url,
                    headers=self.headers,
                    callback=self.parse_captcha_1,
                    dont_filter=True,
                    meta={
                        'proxy': PROXY
                    }
                )
        else:
            # Load cookies
            cookies = response.request.headers.get("Cookie")
            # Load captcha url
            captcha_url = response.xpath(
                    self.captcha_url_xpath_2).extract_first()
            captcha = self.solve_captcha(
                captcha_url,
                response
            )
            captcha = captcha.lower()
            self.logger.info(
                "Captcha has been solved: %s" % captcha
            )

            token = response.xpath(self.captcha_token_xpath).extract_first()
            formdata = {
                "_token": token,
                "captcha": captcha,
                "name": USERNAME,
                "password": PASSWORD
            }
            self.logger.debug(f'Form data: {formdata}')

            yield FormRequest.from_response(
                response=response,
                formxpath=self.login_form_xpath,
                formdata=formdata,
                headers=self.headers,
                callback=self.parse_start,
                dont_filter=True,
                meta=self.synchronize_meta(response),
            )

    def parse_start(self, response):

        if response.xpath(self.captcha_url_xpath_2):
            self.logger.info("Invalid Captcha")
            return
        
        market_url = self.base_url + '/items/category/all-items'
        yield Request(
            url=market_url,
            headers=self.headers,
            callback=self.parse_products,
            meta=self.synchronize_meta(response),
            dont_filter=True
        )

class TorrezScrapper(SiteMapScrapper):
    spider_class = TorrezSpider
    site_name = 'torrez'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


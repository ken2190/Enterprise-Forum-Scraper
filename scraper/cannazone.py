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


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'

PROXY = 'http://127.0.0.1:8118'
NO_OF_THREADS=1

class CannaZoneSpider(MarketPlaceSpider):

    name = "cannazone_spider"

    # Url stuffs
    base_url = "http://cannazonceujdye3.onion"

    # xpath stuffs
    captch_form_xpath = '//form[@method="POST"]'
    captcha_url_xpath = '//img[contains(@src, "/captcha/")]/@src'
    market_url_xpath = '//a[contains(@href, "/products?category=")]/@href'
    product_url_xpath = '//a[contains(@class, "product_name_text")]/@href'

    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//div[contains(@class, "product-information-vendor")]//a[contains(@class, "vendor_rating")]/@href'
    avatar_xpath = '//img[contains(@class, "img-responsive")]/@src'

    login_failed_xpath = '//div[@class="note" and contains(., "Incorrect username or password")]'
    captcha_failed_xpath = '//span[contains(@class, "help-block") and contains(., "Captcha code is incorrect")]'

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
    retry_http_codes = [406, 429, 500, 503]
    download_thread = NO_OF_THREADS
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def get_file_id(self, url):
        return url.split("/products/")[1].strip("/").replace("/", '-')

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
            errback=self.check_site_error,
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
        self.logger.debug(f'Form data: {formdata}')

        yield FormRequest.from_response(
            response=response,
            formxpath=self.captch_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_start,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse_start(self, response):

        # Check if bypass captcha failed
        self.check_if_captcha_failed(response, self.captcha_failed_xpath)

        market_url = self.base_url + '/products'
        yield Request(
            url=market_url,
            headers=self.headers,
            callback=self.parse_products,
            meta=self.synchronize_meta(response),
            dont_filter=True
        )

class CannaZoneScrapper(SiteMapScrapper):
    spider_class = CannaZoneSpider
    site_name = 'cannazone'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


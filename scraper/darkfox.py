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


class DarkFoxSpider(MarketPlaceSpider):

    name = "darkfox_spider"

    # Url stuffs
    base_url = "http://57d5j6hfzfpsfev6c7f5ltney5xahudevvttfmw4lrtkt42iqdrkxmqd.onion/"

    # xpath stuffs
    captch_form_xpath = '//form[@method="post"]'
    captcha_url_xpath_1 = '//div[@class="imgWrap"]/@style'
    captcha_url_xpath_2 = '//img[contains(@class, "captcha")]/@src'
    market_url_xpath = '//input[@name="category[]"]/@value'
    product_url_xpath = '//div[@class="media-content"]/a[contains(@href, "/product/")]/@href'

    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//h3[contains(., "Vendor:")]/a/@href'
    user_description_xpath = '//div[@class="tabs"]//a[contains(@href, "/about")]/@href'
    user_pgp_xpath = '//div[@class="tabs"]//a[contains(@href, "/pgp")]/@href'
    avatar_xpath = '//ul[@class="slides"]//img[contains(@class, "slide-main")]/@src'

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
            callback=self.parse_captcha_1,
            dont_filter=True,
            meta={
                'proxy': PROXY,
                'handle_httpstatus_list': [302]
            }
        )

    def get_market_url(self, category_id):
        return f'{self.base_url}category/{category_id}'

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

        formdata = {
            "cap": captcha
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

    def parse_captcha_2(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        if response.xpath(self.captcha_url_xpath_1):
            self.logger.info("Invalid Captcha")
            return

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

        token = response.xpath('//input[@name="_token"]/@value').extract_first()
        formdata = {
            "_token": token,
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

        if response.xpath(self.captcha_url_xpath_2):
            self.logger.info("Invalid Captcha")
            return
        yield from super().parse_start(response)


class DarkFoxScrapper(SiteMapScrapper):
    spider_class = DarkFoxSpider
    site_name = 'darkfox (57d5j6hfzfpsfev6c7f5ltney5xahudevvttfmw4lrtkt42iqdrkxmqd)'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


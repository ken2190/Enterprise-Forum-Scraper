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


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"

PROXY = 'http://127.0.0.1:8118'


class DarkBaySpider(MarketPlaceSpider):

    name = "darkbay_spider"

    # Url stuffs
    base_url = "http://darkbayupenqdqvv.onion/"

    # xpath stuffs
    login_form_xpath = '//form[@method="POST"]'
    captcha_url_xpath = '//form[@method="POST"]//img/@src'
    market_url_xpath = '//div[@class="category"]/a/@href'
    product_url_xpath = '//a[contains(@href, "/product/")]/@href'
    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//a[contains(@href, "/vendor/")]/@href'
    avatar_xpath = '//img[contains(@class, "image-responsive")]/@src'
    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

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

    def get_user_id(self, url):
        return url.rsplit('vendor/', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('product/', 1)[-1]

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
        cookies = response.request.headers.get("Cookie").decode("utf-8")
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
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
            "captcha": captcha
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


class DarkbayScrapper(SiteMapScrapper):
    spider_class = DarkBaySpider
    site_name = 'darkbay (darkbayupenqdqvv.onion)'

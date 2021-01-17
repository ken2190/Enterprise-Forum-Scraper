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


class TorSpider(MarketPlaceSpider):

    name = "tor_spider"

    # Url stuffs
    base_url = "http://tt2mopgckifmberr.onion"
    login_url = "http://tt2mopgckifmberr.onion/sessions/new"

    # xpath stuffs
    login_form_xpath = '//form[@method="post"]'
    login_utf8_xpath = '//input[@name="utf8"]/@value'
    token_xpath = '//input[@name="authenticity_token"]/@value'

    product_url_xpath = '//tr[@class="product"]//a[contains(@href, "/products/")]/@href'

    next_page_xpath = '//a[@rel="next"]/@href'
    user_xpath = '//div[contains(@class, "media-body")]//a[contains(@href, "/profiles/")]/@href'
    avatar_xpath = '//div[@class="productimage"]//img/@src'

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

        utf8 = response.xpath(self.login_utf8_xpath).extract_first()
        token = response.xpath(self.token_xpath).extract_first()
        formdata = {
            "utf8": utf8,
            "authenticity_token": token,
            "username": USERNAME,
            "password": PASSWORD,
            "commit": "Login"
        }
        self.logger.debug(f'Form data: {formdata}')

        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_products,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

class TorScrapper(SiteMapScrapper):
    spider_class = TorSpider
    site_name = 'tor'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)


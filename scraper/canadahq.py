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

USERNAME = "thecreator"
PASSWORD = "Chq#Blast888"
KEY = "aiJZHkxlNhTiQA8orj8y"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"


class CanadaHQSpider(MarketPlaceSpider):

    name = "canadahq_spider"

    # Url stuffs
    base_url = "https://canadahq.net/"
    login_url = "https://canadahq.net/login"

    # Css stuffs
    captcha_url_css = "div>img[src*=captcha]::attr(src)"

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
    use_proxy = True
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

    def start_requests(self):
        # Synchronize user agent for cloudfare middleware

        yield Request(
            url=self.login_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_login
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        # Load cookies
        cookies = response.request.headers.get("Cookie", '').decode("utf-8")
        if "XSRF-TOKEN" not in cookies:
            yield from self.start_requests()
            return

        # Load captcha url
        captcha_url = response.css(self.captcha_url_css).extract_first()
        captcha = self.solve_captcha(
            captcha_url,
            response
        )
        if len(captcha) > 5:
            captcha = captcha.replace('l', '').replace('^', '')

        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        # token obtain
        token = response.xpath('//input[@name="_token"]/@value').extract_first()
        formdata = {
            "username": USERNAME,
            "password": PASSWORD,
            "captcha": captcha[:5],
            "_token": token
        }
        self.logger.info(f'Formdata is {formdata}')
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_start,
            dont_filter=True
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        # Check valid captcha
        is_invalid_captcha = response.xpath(
            self.invalid_captcha_xpath).extract_first()
        if is_invalid_captcha:
            self.logger.info(
                "Invalid captcha."
            )

            yield Request(
                url=self.login_url,
                headers=self.headers,
                dont_filter=True,
                callback=self.parse_login,
            )
            return

        yield from super().parse_start(response)


class CanadaHQScrapper(SiteMapScrapper):
    spider_class = CanadaHQSpider
    site_name = 'canadahq.at'

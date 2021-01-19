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


USERNAME = "blastedone"
PASSWORD = "Chq#Blast888"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"

PROXY = 'http://127.0.0.1:8118'


class ApollonSpider(MarketPlaceSpider):

    name = "apollon_spider"

    # Url stuffs
    base_url = "http://apollionih4ocqyd.onion/"
    login_url = f"{base_url}login.php"

    # xpath stuffs
    login_form_xpath = captcha_form_xpath = '//form[@method="POST"]'
    login_alert_xpath = '//div[contains(@class, "alert alert-danger")]/text()'

    captcha_url_xpath = '//img[@name="capt_code"]/@src'
    market_url_xpath = '//ul[@id="side-menu"]/li/a/@href'
    product_url_xpath = '//a[contains(@href, "listing.php")]/@href'
    
    next_page_xpath = '//li[@class="page-item active"]'\
                      '/following-sibling::li[1]/a/@href'
    user_xpath = '//small/a[contains(@href, "user.php")]/@href'
    user_description_xpath = '//ul[contains(@class, "nav nav-tabs")]//a[contains(@href, "tab=1")]/@href'
    user_pgp_xpath = '//ul[contains(@class, "nav nav-tabs")]//a[contains(@href, "tab=6")]/@href'
    avatar_xpath = '//img[contains(@class, "img-rounded")]/@src'

    # Login Failed Message xpath
    login_failed_xpath = '//div[contains(@class, "alert alert-danger") and contains(., "username and/or password")]'
    captcha_failed_xpath = '//div[contains(@class, "alert alert-danger") and contains(., "The Captcha code")]'

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
    use_proxy = "Tor"
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

    def get_market_url(self, url):
        base_url = f'{self.base_url}home.php'
        if base_url not in url:
            url = base_url + url
        return url

    def get_user_id(self, url):
        return url.rsplit('id=', 1)[-1]

    def get_file_id(self, url):
        return url.rsplit('id=', 1)[-1]

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            errback=self.check_site_error,
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
                "Referer": f"{self.base_url}login.php",
                "Host": "apollionih4ocqyd.onion"
            }
        )
        captcha = captcha.lower()
        self.logger.info(
            "Captcha has been solved: %s" % captcha
        )

        formdata = {
            'l_username': USERNAME,
            'l_password': PASSWORD,
            "capt_code": captcha
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

        # Check if bypass captcha failed
        self.check_if_captcha_failed(response, self.captcha_failed_xpath)

        yield from super().parse_start(response)


class ApollonScrapper(SiteMapScrapper):
    spider_class = ApollonSpider
    site_name = 'apollon (apollionih4ocqyd.onion)'
    site_type = 'marketplace'

    def __init__(self, kwargs):
        kwargs['get_users'] = True
        super().__init__(kwargs)
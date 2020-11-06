import os
import re
import time
import uuid
import json

from datetime import datetime
from scrapy.utils.gz import gunzip

from selenium.webdriver import (
    Chrome,
    ChromeOptions
)
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper,
    PROXY_USERNAME,
    PROXY_PASSWORD,
    PROXY
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USERNAME = "umeshpathak@protonmail.com"
PASSWORD = "4hr63yh38a61SDW0"

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/81.0.4044.138 Safari/537.36'


class NulledChSpider(SitemapSpider):
    name = 'nulledch_spider'

    # Url stuffs
    base_url = 'https://www.nulled.ch/'
    login_url = 'https://www.nulled.ch/user-login'
    
    # Xpath stuffs
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = '//a[contains(@href, "forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/div/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/div[@class="lastpost smalltext"]/text()[1]|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/div[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//div[@class="post_content"]/preceding-sibling::'\
                      'span[1]/text()[1]|//div[@class="post_content"]'\
                      '/preceding-sibling::span[1]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@class="g-recaptcha"]/@data-sitekey'

    # Regex stuffs
    topic_pattern = re.compile(
        r'thread-(\d+)',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            'User-Agent': USER_AGENT
        })

    def get_cookies(self, use_proxy=False):
        # Init options
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        if use_proxy:
            proxy = PROXY % (PROXY_USERNAME, PROXY_PASSWORD)
            options.add_argument(f'--proxy-server={proxy}')
        options.add_argument(f'user-agent={USER_AGENT}')

        # Init web driver arguments
        webdriver_kwargs = {
            "executable_path": "/usr/local/bin/chromedriver",
            "options": options
        }
        browser = Chrome(**webdriver_kwargs)
        browser.get(self.login_url)
        time.sleep(20)
        cookies = browser.get_cookies()
        browser.quit()
        bypass_cookies = {
            c.get("name"): c.get("value") for c in cookies
        }
        return bypass_cookies

    def start_requests(self):
        cookies = self.get_cookies(self.use_proxy)
        yield Request(
            url=self.login_url,
            callback=self.proceed_for_login,
            headers=self.headers,
            dont_filter=True,
            cookies=cookies,
        )

    def proceed_for_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        my_post_key = response.xpath(
            '//input[@name="my_post_key"]/@value').extract_first()
        self.logger.info('my_post_key')
        self.logger.info(my_post_key)
        formdata = {
            "username": USERNAME,
            "password": PASSWORD,
            "remember": "yes",
            "submit": "Login",
            "action": "do_login",
            "url": "",
            "g-recaptcha-response": self.solve_recaptcha(response),
            "my_post_key": my_post_key
        }
        self.logger.info(formdata)
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        if not all_forums:
            self.logger.info(response.text)
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            if 'forum-178.html' not in forum_url:
                continue

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class NulledChScrapper(SiteMapScrapper):

    spider_class = NulledChSpider
    site_name = 'nulled.ch'
    site_type = 'forum'

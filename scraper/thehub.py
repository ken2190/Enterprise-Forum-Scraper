import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
import hashlib
from scrapy.http import Request, FormRequest

from datetime import datetime

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USER = "vrx9"
PASS = "Night#Hub998"

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class TheHubSpider(SitemapSpider):
    name = 'thehub_spider'
    base_url = 'http://thehub5himseelprs44xzgfrb4obgujkqwy5tzbsh5yttebqhaau23yd.onion/index.php'

    # Xpaths
    forum_xpath = '//a[contains(@href, "index.php?board=")]/@href'
    pagination_xpath = '//div[@class="pagelinks floatleft"]'\
                       '/strong/following-sibling::a[1]/@href'
    thread_xpath = '//div[@id="messageindex"]//tr[td[contains(@class,"subject")]]'
    thread_first_page_xpath = '//span[contains(@id,"msg_")]/a/@href'
    thread_last_page_xpath = '//small[contains(@id,"pages")]'\
                             '/a[not(text()="All")][last()]/@href'
    thread_date_xpath = '//td[contains(@class, "lastpost")]/br'\
                        '/preceding-sibling::text()[1]'
    thread_pagination_xpath = '//div[@class="pagelinks floatleft"]'\
                              '/strong/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//div[@class="pagelinks floatleft"]'\
                        '/strong/text()'
    post_date_xpath = '//div[@class="keyinfo"]'\
                      '/div[@class="smalltext"]/text()[last()]'

    avatar_xpath = '//li[@class="avatar"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"attach=(\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = "%B %d, %Y, %I:%M:%S %p"
    post_datetime_format = "%B %d, %Y, %I:%M:%S %p »"
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.base_url,
            callback=self.proceed_for_login,
            headers=self.headers,
            meta={
                'proxy': PROXY
            }
        )

    def proceed_for_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        token = response.xpath(
            '//p[@class="centertext smalltext"]/'
            'following-sibling::input[1]'
        )
        if not token:
            return
        token_key = token[0].xpath('@name').extract_first()
        token_value = token[0].xpath('@value').extract_first()
        form_data = {
            "cookieneverexp": "on",
            "hash_passwrd": "",
            "passwrd": PASS,
            "user": USER,
            token_key: token_value,
        }
        login_url = f'{self.base_url}?action=login2'
        yield FormRequest(
            url=login_url,
            headers=self.headers,
            formdata=form_data,
            callback=self.parse_start,
            meta=self.synchronize_meta(response),
            dont_filter=True,
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if 'at ' in thread_date.lower():
            return datetime.today()
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()

        if "at " in post_date.lower():
            return datetime.today()
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
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

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class TheHubScrapper(SiteMapScrapper):

    spider_class = TheHubSpider
    site_name = 'majestic_garden'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

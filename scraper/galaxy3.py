import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
import locale
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.2
NO_OF_THREADS = 10

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class Galaxy3Spider(SitemapSpider):
    name = 'galaxy3_spider'
    start_url = 'http://galaxy3m2mn5iqtn.onion/thewire/all'
    base_url = 'http://galaxy3m2mn5iqtn.onion'

    # Xpaths
    pagination_xpath = '//li/a[contains(text(), "Next")]/@href'
    thread_xpath = '//ul[contains(@class, "elgg-list")]/li'
    thread_first_page_xpath = './/a[contains(text(), "Thread") and '\
                              'contains(@href, "thewire/thread/")]/@href'
    thread_date_xpath = './/div/time[@datetime]/@datetime'
    thread_pagination_xpath = '//li/a[contains(text(), "Next")]/@href'
    thread_page_xpath = '//li[@class="elgg-state-selected"]/span/text()'
    post_date_xpath = '//div/time[@datetime]/@datetime'

    avatar_xpath = '//div[contains(@class,"elgg-avatar")]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"thread/(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse_forum,
            headers=self.headers,
            meta={
                'proxy': PROXY
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

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        return datetime.strptime(
            thread_date.strip()[:-6],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-6],
            self.post_datetime_format
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class Galaxy3Scrapper(SiteMapScrapper):

    spider_class = Galaxy3Spider
    site_name = 'galaxy3_lgalaxy3m2mn5iqtn'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

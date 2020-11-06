import os
import re
import time
import uuid
import json
from lxml.html import fromstring
from urllib.parse import urlencode
from datetime import datetime, timedelta

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 12

USER = "Cyrax011"
PASS = "4hr63yh38a61SDW0"


class DssLegendsSpider(SitemapSpider):
    name = 'dsslegends_spider'

    # Url stuffs
    base_url = "https://www.dsslegends.com"

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = '//div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = '//span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Other settings
    use_proxy = True
    handle_httpstatus_list = [403]
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r'threads/.*\.(\d+)/',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    def start_requests(self):
        yield Request(
            url=f'{self.base_url}/forums',
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': '',
            '_xfToken': token
        }
        yield FormRequest(
            url="https://www.dsslegends.com/forums/index.php?login/login",
            callback=self.parse_start,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        return datetime.strptime(
            thread_date.strip()[:-5],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-5],
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


class DssLegendsScrapper(SiteMapScrapper):

    spider_class = DssLegendsSpider
    site_name = 'dsslegends.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [403, 406, 429, 500, 503]
        })
        return settings

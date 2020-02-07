import sys
import os
import re
import json
import scrapy
from glob import glob
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import (
    datetime,
    timedelta
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USER = 'blacklotus2000@protonmail.com'
PASS = 'Night#Anti999'
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class AntichatSpider(SitemapSpider):
    name = 'antichat_spider'
    # Xpath stuffs
    forum_xpath = '//div[@class="nodelistBlock nodeText"]'\
                  '/h3[@class="nodeTitle"]/a/@href|'\
                  '//ol[@class="subForumList"]'\
                  '//h4[@class="nodeTitle"]/a/@href'

    pagination_xpath = '//a[@class="text" and text()="Next >"]/@href'

    thread_xpath = '//li[contains(@class,"discussionListItem ")]'
    thread_first_page_xpath = '//h3[@class="title"]/a/@href'
    thread_last_page_xpath = '//span[@class="itemPageNav"]/a[last()]/@href'
    thread_date_xpath = '//dl[@class="lastPostInfo"]//span[@class="DateTime"]'\
                        '/@title|//dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/text()'
    thread_page_xpath = '//nav/a[contains(@class,"currentPage")]/text()'
    thread_pagination_xpath = '//nav/a[contains(text()," Prev")]/@href'

    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/@title|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/text()'

    avatar_xpath = '//a[@data-avatarhtml="true"]/img/@src'

    # Other settings
    sitemap_datetime_format = '%d %b %Y at %H:%M %p'
    post_datetime_format = '%d %b %Y at %H:%M %p'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'https://forum.antichat.ru/'
        self.topic_pattern = re.compile(r'/threads/(\d+)/')
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.pagination_pattern = re.compile(r'page-(\d+)')
        self.headers = {
            'origin': 'https://forum.antichat.ru',
            'referer': 'https://forum.antichat.ru/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': USER_AGENT,
        }

    def proceed_for_login(self):
        login_url = 'https://forum.antichat.ru/login/login'
        params = {
            'login': USER,
            'password': PASS,
            'register': '0',
            "remember": '1',
            'cookie_check': '1',
            'redirect': 'https://forum.antichat.ru/',
            '_xfToken': ''
        }
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse(self, response):

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
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class AntichatScrapper(SiteMapScrapper):

    spider_class = AntichatSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return settings

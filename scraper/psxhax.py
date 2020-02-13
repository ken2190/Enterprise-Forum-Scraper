import time
import requests
import os
import json
import re
import scrapy
from math import ceil
import configparser
from urllib.parse import urlencode
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USER = 'Cyrax011'
PASS = 'Night#PSxHAx000'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) '\
             'AppleWebKit/537.36 (KHTML, like Gecko) '\
             'Chrome/79.0.3945.117 Safari/537.36',


class PsxhaxSpider(SitemapSpider):
    name = 'psxhax_spider'

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href'
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
    post_date_xpath = '//div[@class="message-attribution-main"]'\
                      '/a/span[@class="u-concealed"]/@title|'\
                      '//div[@class="p-body-header"]'\
                      '//a[@class="u-concealed"]/@title'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Other settings
    use_proxy = False
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'
    post_datetime_format = '%b %d, %Y at %I:%M %p'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://www.psxhax.com"
        self.topic_pattern = re.compile(r'threads/.*\.(\d+)/')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*/page-(\d+)')
        self.headers.update({
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT
        })

    def parse_thread_date(self, thread_date):

        return datetime.strptime(
            thread_date.strip()[:-6],
            self.sitemap_datetime_format
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load token
        match = re.findall(r'csrf: \'(.*?)\'', response.text)

        # Load param
        params = {
            '_xfRequestUri': '/',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        token_url = 'https://psxhax.com/login/?' + urlencode(params)
        yield Request(
            url=token_url,
            headers=self.headers,
            callback=self.proceed_for_login,
            meta=self.synchronize_meta(response)
        )

    def proceed_for_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load json data
        json_response = json.loads(response.text)
        html_response = fromstring(json_response['html']['content'])

        # Exact token
        token = html_response.xpath(
            '//input[@name="_xfToken"]/@value')[0]

        # Load params
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': 'https://www.psxhax.com/forums/',
            '_xfToken': token
        }
        login_url = 'https://psxhax.com/login/login'
        yield FormRequest(
            url=login_url,
            callback=self.parse_main_page,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response)
            )

    def parse_main_page(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'buy-sell-and-trade.24' not in forum_url:
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class PsxhaxScrapper(SiteMapScrapper):

    spider_class = PsxhaxSpider
    site_name = 'psxhax.com'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS
            }
        )
        return spider_settings

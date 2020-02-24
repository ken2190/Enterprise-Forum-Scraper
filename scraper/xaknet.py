import os
import re
import time
import uuid
import json
from urllib.parse import urlencode
from lxml.html import fromstring

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


REQUEST_DELAY = 0.5
NO_OF_THREADS = 2

USER = 'vrx9'
PASS = '4hr63yh38a'


class XaknetSpider(SitemapSpider):
    name = 'xaknet_spider'

    # Url stuffs
    base_url = "https://xaknet.org"

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//div[contains(@class,"node-description")]/span/a/@href'
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
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/(\d+)/",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
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

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load token
        match = re.findall(r'csrf: \'(.*?)\'', response.text)

        # Load param
        params = {
            '_xfRequestUri': '/forum',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        token_url = 'https://xaknet.org/forum/login/?' + urlencode(params)
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
            '_xfRedirect': 'https://xaknet.org/forum/',
            '_xfToken': token
        }
        login_url = 'https://xaknet.org/forum/login/login'
        yield FormRequest(
            url=login_url,
            callback=self.parse_start,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response)
            )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'forums/2/' not in forum_url:
            #     continue
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


class XaknetScrapper(SiteMapScrapper):

    spider_class = XaknetSpider
    site_name = 'xaknet.org'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

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
from datetime import datetime, timedelta
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class SoqorSpider(SitemapSpider):
    name = 'soqor_spider'
    base_url = 'https://forums.soqor.net/'

    # Xpaths
    forum_xpath = '//a[@class="forum-title"]/@href|'\
                  '//a[@class="subforum-title"]/@href'
    thread_xpath = '//tr[contains(@class, "topic-item ")]'
    thread_first_page_xpath = './/a[contains(@class,"topic-title ")]/@href'
    thread_last_page_xpath = './/a[contains(@class,"pagenav-last-button")]/@href'
    thread_date_xpath = './/span[@class="post-date"]/text()'
    pagination_xpath = '//a[contains(@class, "pagenav-next-button") '\
                       'and not(contains(@class,"h-hide"))]/@href'
    thread_pagination_xpath = '//a[contains(@class,"pagenav-current-button")]'\
                              '/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//a[contains(@class,"pagenav-current-button")]/text()'
    post_date_xpath = '//time[@itemprop="dateCreated"]/@datetime'

    avatar_xpath = '//a[contains(@class,"avatar--thread")]/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r'.*/(\d+)-',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%m-%d-%Y, %I:%M %p'
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip().strip(',')
        days = None
        if 'ساعات' in thread_date.lower():
            # hours
            days = 0
        elif 'أسبوع' in thread_date.lower():
            # week
            days = 7
        elif 'يوم' in thread_date.lower():
            # days
            match = re.findall(r'\d+', thread_date.lower())
            days = int(match[0])
        elif 'أسابيع' in thread_date.lower():
            # weeks
            match = re.findall(r'\d+', thread_date.lower())
            days = int(match[0]) * 7
        if days is not None:
            return datetime.today() - timedelta(days=days)
        return datetime.strptime(
            thread_date,
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        post_date = post_date.strip().strip(',')
        days = None
        if 'ساعات' in post_date.lower():
            # hours
            days = 0
        elif 'أسبوع' in post_date.lower():
            # week
            days = 7
        elif 'يوم' in post_date.lower():
            # days
            match = re.findall(r'\d+', post_date.lower())
            days = int(match[0])
        elif 'أسابيع' in post_date.lower():
            # weeks
            match = re.findall(r'\d+', post_date.lower())
            days = int(match[0]) * 7
        if days is not None:
            return datetime.today() - timedelta(days=days)
        return datetime.strptime(
            post_date,
            self.post_datetime_format
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check current page and last page
        current_page = response.xpath(self.thread_page_xpath).extract_first() or 1
        last_page = response.xpath(self.topic_last_page_xpath).extract_first()

        # Reverse scraping start here
        if int(current_page) == 1 and last_page:
            if self.base_url not in last_page:
                last_page = self.base_url + last_page
            yield Request(
                url=last_page,
                headers=self.headers,
                callback=super().parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": response.meta.get("topic_id")
                    }
                )
            )

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath).extract()
        for avatar_url in all_avatars:

            avatar_url = avatar_url.strip('.').split('..')[-1]

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )


class SoqorScrapper(SiteMapScrapper):

    spider_class = SoqorSpider
    site_name = 'forums.soqor.net'
    site_type = 'forum'

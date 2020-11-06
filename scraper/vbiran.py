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


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class VBIranSpider(SitemapSpider):
    name = 'vbiran_spider'
    base_url = 'http://www.vbiran.ir/'

    # Xpaths
    forum_xpath = '//div[@class="datacontainer"]'\
                  '//h2[@class="forumtitle"]/a[contains(@href, "/forum")]/@href|'\
                  '//li[@class="subforum"]/a[contains(@href, "/forum")]/@href'
    thread_xpath = '//li[contains(@class, "threadbit ")]'
    thread_first_page_xpath = './/a[contains(@id,"thread_title_")]/@href'
    thread_last_page_xpath = './/dl[@class="pagination"]/dd'\
                             '/span[last()]/a/@href'
    thread_date_xpath = './/dl[@class="threadlastpost td"]'\
                        '//dd[last()]/text()[1]'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//span[@class="selected"]/a/text()'
    post_date_xpath = '//span[@class="date"]/text()[1]'

    avatar_xpath = '//a[contains(@class,"postuseravatar")]/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r'thread(\d+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%Y/%m/%d'
    post_datetime_format = '%Y/%m/%d'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip().strip(',')
        if 'امروز' in thread_date.lower():
            return datetime.today()
        elif 'دیروز' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.strip().strip(',')
        if 'امروز' in post_date.lower():
            return datetime.today()
        elif 'دیروز' in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

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

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class VBIranScrapper(SiteMapScrapper):

    spider_class = VBIranSpider
    site_name = 'vbiran.ir'
    site_type = 'forum'

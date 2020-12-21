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


class AntiOnlineSpider(SitemapSpider):
    name = 'antionline_spider'
    base_url = 'http://www.antionline.com/'

    # Xpaths
    forum_xpath = '//div[@class="datacontainer"]'\
                  '//h2[@class="forumtitle"]/a/@href|'\
                  '//li[@class="subforum"]/a/@href'
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

    avatar_xpath = '//a[@class="postuseravatar"]/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r'.*u=(\w+)\&',
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r'showthread\.php\?(\d+)-',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%B %d, %Y'
    post_datetime_format = '%B %d, %Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip().strip(',')
        thread_date = re.sub(r' (\d+)[a-z]+', ' \\1', thread_date)
        if any(i in thread_date.lower() for i in ['hour', 'today']):
            return datetime.today()
        elif 'yesterday' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.strip().strip(',')
        post_date = re.sub(r' (\d+)[a-z]+', ' \\1', post_date)
        if any(i in post_date.lower() for i in ['hour', 'today']):
            return datetime.today()
        elif 'yesterday' in post_date.lower():
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
            # if '84-Regulatory-Compliance' not in forum_url:
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

    def get_avatar_file(self, url=None):
        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class AntiOnlineScrapper(SiteMapScrapper):

    spider_class = AntiOnlineSpider
    site_name = 'antionline.com'
    site_type = 'forum'

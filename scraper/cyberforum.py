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


class CyberForumSpider(SitemapSpider):
    name = 'cyberforum_spider'
    base_url = 'https://www.cyberforum.ru/'

    # Xpaths
    forum_xpath = '//td/div/a[span[@class="forumtitle"]]/@href|'\
                  '//td/img[contains(@id,"forum_statusicon_")]'\
                  '/following-sibling::a[1]/@href'
    thread_xpath = '//tr[contains(@id, "vbpostrow_")]'
    thread_first_page_xpath = '//a[contains(@id,"thread_title_")]/@href'
    thread_last_page_xpath = '//td[contains(@id,"td_threadtitle_")]'\
                             '/div/span/a[last()]/@href'
    thread_date_xpath = '//span[@class="time"]/preceding-sibling::text()'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//td[@class="alt2 smallfont"]/text()[1]'

    # Regex stuffs
    topic_pattern = re.compile(
        r'thread(\d+)',
        re.IGNORECASE
    )

    # Other settings
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d.%m.%Y'
    post_datetime_format = '%d.%m.%Y'

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if 'сегодня' in thread_date.lower():
            return datetime.today()
        elif "вчера" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
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
        post_date = post_date.split(',')[0].strip()

        if "сегодня" in post_date.lower():
            return datetime.today()
        elif "вчера" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        elif not re.match(r'\d{2}.\d{2}.\d{4}', post_date):
            return
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


class CyberForumScrapper(SiteMapScrapper):

    spider_class = CyberForumSpider
    site_name = 'cyberforum.ru'

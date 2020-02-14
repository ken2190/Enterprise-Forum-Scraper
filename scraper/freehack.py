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

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'


class FreeHackSpider(SitemapSpider):
    name = 'freehack_spider'

    # Xpaths
    forum_xpath = '//div[@class="datacontainer"]'\
                  '//h2[@class="forumtitle"]/a/@href|'\
                  '//li[@class="subforum"]/a/@href'
    thread_xpath = '//li[contains(@class, "threadbit ")]'
    thread_first_page_xpath = '//a[contains(@id,"thread_title_")]/@href'
    thread_last_page_xpath = '//dl[@class="pagination"]/dd'\
                             '/span[last()]/a/@href'
    thread_date_xpath = '//dl[@class="threadlastpost td"]'\
                        '//dd[last()]/text()[1]'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//span[@class="selected"]/a/text()'
    post_date_xpath = '//span[@class="date"]/text()[1]'

    avatar_xpath = '//a[@class="postuseravatar"]/img/@src'

    # Other settings
    use_proxy = False
    sitemap_datetime_format = '%d.%m.%Y,'
    post_datetime_format = '%d.%m.%Y,'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://free-hack.com/"
        self.topic_pattern = re.compile(r'showthread\.php\?(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*u=(\w+)\&')
        self.pagination_pattern = re.compile(r'.*/page(\d+)')
        self.headers.update({
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT
        })

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if '761-Konzepte-und-Vorstellungen' not in forum_url:
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
        # yield from super().parse_avatars(response)

    def get_avatar_file(self, url=None):
        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class FreeHackScrapper(SiteMapScrapper):

    spider_class = FreeHackSpider
    site_name = 'free-hack.com'

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

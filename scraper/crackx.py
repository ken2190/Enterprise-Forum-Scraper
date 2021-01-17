import os
import re
import time
import uuid
import json

from datetime import datetime
from scrapy.utils.gz import gunzip

from seleniumwire.webdriver import (
    Chrome,
    ChromeOptions
)
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class CrackXSpider(SitemapSpider):
    name = 'crackx_spider'

    # Url stuffs
    base_url = "https://crackx.to/"
    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[contains(@class,"post_date")]/text()[1]|'\
                      '//span[contains(@class,"post_date")]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()
        if not thread_date:
            return

        return datetime.strptime(
            thread_date,
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return
        return datetime.strptime(
            post_date,
            self.post_datetime_format
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

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
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CrackXScrapper(SiteMapScrapper):

    spider_class = CrackXSpider
    site_name = 'crackx.to'
    site_type = 'forum'

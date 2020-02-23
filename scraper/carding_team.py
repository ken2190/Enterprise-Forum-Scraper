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


REQUEST_DELAY = 0.6
NO_OF_THREADS = 2


class CardingTeamSpider(SitemapSpider):
    name = 'cardingteam_spider'

    # Url stuffs
    base_url = "https://cardingteam.cc/"
    sitemap_url = 'https://cardingteam.cc/sitemap-index.xml'

    # Sitemap Stuffs
    forum_sitemap_xpath = '//sitemap[loc[contains(text(),"sitemap-threads.xml")] and lastmod]/loc/text()'
    thread_sitemap_xpath = '//url[loc[contains(text(),"Thread-")] and lastmod]'
    thread_url_xpath = '//loc/text()'
    thread_lastmod_xpath = "//lastmod/text()"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        '//td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date2"]/text()[1]|'\
                      '//span[@class="post_date2"]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False

    def start_requests(self):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load cookies
        cookies, ip = self.get_cookies(proxy=self.use_proxy)

        if self.start_date and self.sitemap_url:
            yield Request(
                url=self.sitemap_url,
                headers=self.headers,
                cookies=cookies,
                dont_filter=True,
                callback=self.parse_sitemap,
                meta={
                    "ip": ip
                }
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers,
                dont_filter=True,
                cookies=cookies,
                meta={
                    "ip": ip
                }
            )

    def parse_thread_date(self, thread_date):
        return datetime.today()

    def parse_post_date(self, thread_date):
        return datetime.today()

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
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CardingTeamScrapper(SiteMapScrapper):

    spider_class = CardingTeamSpider
    site_name = 'cardingteam.cc'

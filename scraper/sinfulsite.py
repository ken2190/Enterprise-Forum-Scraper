import time
import os
import re
import scrapy
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class SinfulSiteSpider(SitemapSpider):
    name = 'sinfulsite_spider'
    base_url = "https://sinfulsite.com/"

    # Xpaths
    forum_xpath = '//div[@class="flex-grow"]//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="next"]/@href'
    thread_xpath = '//div[@class="layer forumdisplay" and not(@style)]'
    thread_first_page_xpath = '//span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = '//div[@class="description"]'\
                             '//span[@class="smalltext"]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//div[contains(@class,"latest")]'\
                        '//span[@class="small"]/text()|'\
                        '//div[contains(@class,"latest")]'\
                        '//span[@class="small"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="previous"]/@href'
    thread_page_xpath = '//span[@class="current"]/text()'
    post_date_xpath = '//div[@class="time fullwidth"]/span/@title|'\
                      '//div[@class="time fullwidth"]/text()[1]'

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = '%Y-%m-%d, %H:%M:%S'
    post_datetime_format = '%Y-%m-%d, %H:%M:%S'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

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

    def parse_forum(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        sub_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in sub_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )
        yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """
        if 'background=' in url:
            return
        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class SinfulSiteScrapper(SiteMapScrapper):

    spider_class = SinfulSiteSpider
    site_name = 'sinfulsite.com'

import os
import re
import scrapy
from math import ceil
import configparser
import locale
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.7
NO_OF_THREADS = 4


class SysAdminsSpider(SitemapSpider):
    name = 'sysadmins_spider'
    base_url = 'https://sysadmins.ru/'

    # Xpaths
    forum_xpath = '//a[@class="forumlink"]/@href'
    thread_xpath = '//tr[td/span[@class="topictitle"]]'
    thread_first_page_xpath = '//span[@class="topictitle"]/a/@href'
    thread_last_page_xpath = '//span[@class="gensmall"]/a[last()]/@href'
    thread_date_xpath = '//span[@class="postdetails" and a]/text()[1]'
    pagination_xpath = '//span[@class="navbig"]//a[text()="След."]/@href'
    thread_pagination_xpath = '//td[@class="navbig"]/a[text()="Пред."]/@href'
    thread_page_xpath = '//td[@class="navbig"]/b/text()'
    post_date_xpath = '//noindex/following-sibling::span[1]'\
                      '[@class="postdetails"]/text()[1]'

    avatar_xpath = '//span[@class="postdetails"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%a %d %b, %Y %H:%M'
    sitemap_datetime_format = '%a %d %b, %Y %H:%M'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

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

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        post_date = post_date.replace('Добавлено:', '').strip()
        return datetime.strptime(
            post_date,
            self.post_datetime_format
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class SysAdminsScrapper(SiteMapScrapper):

    spider_class = SysAdminsSpider
    site_name = 'sysadmins.ru'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

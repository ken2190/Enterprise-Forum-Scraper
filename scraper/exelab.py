import os
import re
import time
import uuid
import json
import locale
import dateparser

from datetime import datetime
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
NO_OF_THREADS = 10


class ExeLabSpider(SitemapSpider):
    name = 'exelab_spider'

    # Url stuffs
    base_url = "https://exelab.ru/f/"
    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "action=vtopic")]/@href'
    pagination_xpath = '//a[text()=">>"]/@href'
    thread_xpath = '//table[@class="forums"]//'\
                   'tr[@align="center" and td[@class="caption1"]]'
    thread_first_page_xpath = '//td[@class="caption1"]'\
                              '/a[contains(@href, "vthread")]/@href'
    thread_last_page_xpath = '//sup[@class="navCell"]'\
                             '/a[contains(@href, "vthread")][last()]/@href'
    thread_date_xpath = './/td[6]/span[@class="txtSm"]/text()[1]'
    thread_pagination_xpath = '//a[text()="<<"]/@href'
    thread_page_xpath = '//td[@class="tbTransparent"]'\
                        '/span[@class="txtSm"]/b/b/text()'
    post_date_xpath = '//td[@class="caption1 post"]'\
                      '/span[@class="txtSm"]/text()[1]'

    avatar_xpath = '//div[@class="username"]/br/following-sibling::img[1]/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    topic_pattern = re.compile(
        r"topic=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d %B %Y'
    post_datetime_format = '%d %B %Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()
        if not thread_date:
            return
        return dateparser.parse(thread_date)
        # return datetime.strptime(
        #     thread_date,
        #     self.sitemap_datetime_format
        # )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = re.split(
            r'\d{2}:\d{2}', post_date.replace('Создано: ', '').strip())
        if not post_date:
            return
        post_date = post_date[0].strip()
        return dateparser.parse(post_date)
        # return datetime.strptime(
        #     post_date,
        #     self.post_datetime_format
        # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

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


class ExeLabScrapper(SiteMapScrapper):

    spider_class = ExeLabSpider
    site_name = 'exelab.ru'

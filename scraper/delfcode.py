import os
import re
import time
import uuid
import json
import dateparser

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class DelfcodeSpider(SitemapSpider):
    name = 'delfcode_spider'

    # Url stuffs
    base_url = "https://delfcode.ru"
    # Xpath stuffs
    forum_xpath = '//td[@class="forumNameTd"]/a[@class="forum"]/@href'
    pagination_xpath = '//a[@class="switchNext"]/@href'
    thread_xpath = '//tr[td[@class="threadNametd"]]'
    thread_first_page_xpath = './/a[@class="threadLink"]/@href'
    thread_last_page_xpath = './/span[@class="postpSwithces"]'\
                             '/a[@class="postPSwithcesLink"][last()]/@href'
    thread_date_xpath = './/td[@class="threadLastPostTd"]/a/text()[1]'
    thread_pagination_xpath = '//a[@class="switchBack"]/@href'
    thread_page_xpath = '//li[@class="switchActive"]/text()'
    post_date_xpath = '//td[@class="postTdTop" and a[@class="postNumberLink"'\
                      ']]/text()[1]'

    avatar_xpath = '//img[@class="userAvatar"]/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    topic_pattern = re.compile(
        r"forum/\d+-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date.split(',', 1)[-1].split('|')[0].strip()
        return dateparser.parse(post_date)

    def start_requests(self):
        yield Request(
            url=f'{self.base_url}/forum/',
            headers=self.headers,
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
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


class DelfcodeScrapper(SiteMapScrapper):

    spider_class = DelfcodeSpider
    site_name = 'delfcode.ru'
    site_type = 'forum'

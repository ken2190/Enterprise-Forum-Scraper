import os
import re

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import Request, Selector

from datetime import datetime
import dateparser


class NulledBBSpider(SitemapSpider):

    name = 'nulledbb_spider'

    # Url stuffs
    base_url = "https://nulledbb.com/"
    start_urls = ["https://nulledbb.com/"]

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r'.*avatar_(\d+\.\w+)',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )


    # Xpath stuffs
    forum_xpath = '//div[@class="forums-row"]//div[@class="title"]/a/'\
                  '@href|//div[@class="subforums"]//a[@title]/@href'

    thread_xpath = '//div[contains(@class,"wrapper")]//div[contains(@class, "forumdisplay_")]'
    pagination_xpath = '//a[@class="pagination_next"]/@href'
    thread_first_page_xpath = '//span[contains(@id, "tid_")]'\
                              '/a[contains(@href, "thread-")]/@href'
    thread_last_page_xpath = '//a[contains(text(),"Last Post")]/@href'
    thread_date_xpath = '//div[contains(@class,"threadlist-lastpost")]/span/*[last()]/span/@title|'\
                        '//div[contains(@class,"threadlist-lastpost")]/span/*[last()]/text()'

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    thread_page_xpath = '//span[contains(@class,"pagination_current")]/text()'

    thread_pagination_xpath = '//ul[@class="pages"]/li/a[@class="pagination_previous"]/@href'

    post_date_xpath = '//div[contains(@class,"postbit-message-time")]/span/@title|'\
                      '//div[contains(@class,"postbit-message-time")]'\
                      '[contains(string(),"Posted: ")]/text()'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://nulledbb.com/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1"
            }
        )

    def parse_thread_date(self, post_date):
        try:
            date = post_date.split('Posted: ')[-1]
            return dateparser.parse(date).replace(tzinfo=None)
        except:
            return datetime.now()

    def parse_post_date(self, post_date):
        try:
            date = post_date.split('Posted: ')[-1]
            return dateparser.parse(date).replace(tzinfo=None)
        except:
            return datetime.now()

    def parse_thread(self, response):
        yield from super().parse_thread(response)
        yield from super().parse_avatars(response)

class NulledBBScrapper(SiteMapScrapper):

    request_delay = 0.3
    no_of_threads = 12
    spider_class = NulledBBSpider
    site_name = 'nulledbb.com'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            }
        )
        return spider_settings


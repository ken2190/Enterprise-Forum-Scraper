import os
import re

from scrapy.http import Request
from scrapy.exceptions import CloseSpider

from .base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class HackTheBoxSpider(SitemapSpider):
    name = 'hackthebox_scraper'
    base_url = 'https://forum.hackthebox.eu'

    # Xpaths
    forum_xpath = '//a[@class="Title"]/@href|//div[@class="Title"]/a/@href'

    thread_xpath = '//li[contains(@id, "Discussion_")]'
    thread_first_page_xpath = '//div[@class="Title"]/a/@href'
    thread_last_page_xpath = '//span[contains(@class,"LastDiscussionTitle")]/a/@href'
    thread_date_xpath = '//time/@title'

    thread_pagination_xpath = '//div[contains(@id,"PagerAfter")]//a[contains(@rel,"next")]/@href'
    thread_page_xpath = '//*[contains(@id,"PagerAfter")]/a[@aria-current]/text()'

    post_date_xpath = '//time/@title'

    avatar_xpath = '//*[contains(@class, "ProfilePhoto")]/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r"discussion/(\d+)/",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%B %d, %Y %H:%S%p'
    post_datetime_format = '%B %d, %Y %H:%S%p'

    def start_requests(self):
        yield Request(
            url="https://forum.hackthebox.eu/categories",
            headers=self.headers
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def get_forum_next_page(self, response):
        pass

    def parse_thread(self, response):        

        # Load all post date
        yield from super().parse_thread(response)

        yield from super().parse_avatars(response)

class HackTheBoxScrapper(SiteMapScrapper):
    spider_class = HackTheBoxSpider

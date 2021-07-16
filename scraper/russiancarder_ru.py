import re
import os
import uuid

from datetime import datetime, timedelta

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

class RussiancarderRuSpider(SitemapSpider):

    name = "russiancarder_ru_spider"

    # Url stuffs
    base_url = "https://russiancarders.ru/"

    # Xpath stuffs

    # Forum xpath #
    forum_xpath = '//h3[@class="node-title"]/a/@href'
    pagination_xpath = '//a[contains(@class, "pageNav-jump--next") and text()="Next"]/@href'
    thread_xpath = '//div[contains(@class, "structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]/a[last()]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]/@data-time'
    thread_page_xpath = '//nav//li[contains(@class,"pageNav-page--current")]/a/text()'
    thread_pagination_xpath = '//nav//a[contains(text(),"Prev")]/@href'
    post_date_xpath = '//article//time/@data-time'
    avatar_xpath = '//article//a[contains(@class, "avatar")]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    cloudfare_delay = 10
    handle_httpstatus_list = [503]
    sitemap_datetime_format = '%b %d, %Y'
    post_datetime_format = '%b %d, %Y'

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        # print(response.text)
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
                meta=self.synchronize_meta(response)
            )

    def parse_forum(self, response, is_first_page=True):

        # Parse sub forums
        yield from self.parse(response)

        # Parse generic forum
        yield from super().parse_forum(response)
        
    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)

class RussiancarderRuScrapper(SiteMapScrapper):

    spider_class = RussiancarderRuSpider
    site_name = 'russiancarder.ru'
    site_type = 'forum'

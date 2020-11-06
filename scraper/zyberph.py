import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 1
NO_OF_THREADS = 2


class ZyberphSpider(SitemapSpider):
    name = 'zyberph_spider'
    base_url = 'http://www.zyberph.com/'

    # Xpaths
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'
    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = '//a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = '//div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = '//dd[@class="lastpost"]/span/text()[last()]'
    pagination_xpath = '//li[@class="arrow next"]/a[@rel="next"]/@href'
    thread_pagination_xpath = '//li[@class="arrow previous"]/a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination"]//'\
                        'li[@class="active"]/span/text()'
    post_date_xpath = '//p[@class="author"]/text()[last()]'

    avatar_xpath = '//div[@class="avatar-container"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'avatar=(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%a %b %d, %Y %I:%M %p'
    sitemap_datetime_format = '%a %b %d, %Y %I:%M %p'

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()
        if "today" in thread_date.lower():
            return datetime.today()
        elif "yesterday" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()
        if not post_date:
            return

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'f=87' not in forum_url:
            #     continue
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class ZyberphScrapper(SiteMapScrapper):

    spider_class = ZyberphSpider
    site_name = 'zyberph.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

import time
import os
import re
import scrapy
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

class GreysecSpider(SitemapSpider):
    name = 'greysec_spider'
    base_url = "https://greysec.net/"

    # Xpaths
    forum_xpath = '//a[contains(@href, "forumdisplay.php?fid=")]/@href'
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
    post_date_xpath = '//span[@class="post_date"]/text()[1]|'\
                      '//span[@class="post_date"]/span/@title'

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()

        if 'hour' in thread_date.lower():
            return datetime.today()
        elif 'yesterday' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return

        if 'hour' in post_date.lower():
            return datetime.today()
        elif 'yesterday' in post_date.lower():
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


class GreysecScrapper(SiteMapScrapper):

    spider_class = GreysecSpider
    site_name = 'greysec.net'
    site_type = 'forum'

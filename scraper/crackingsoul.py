import re
import dateparser
import dateutil.parser as dparser

from datetime import datetime
from scrapy import Request
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class CrackingSoulSpider(SitemapSpider):
    name = 'crackingsoul_spider'

    # Url stuffs
    base_url = "https://crackingsoul.com/"
    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "Forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/div/div/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/div/span[@class="lastpost smalltext"]/text()|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/div/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[contains(@class,"post_date")]/text()[1]|'\
                      '//span[contains(@class,"post_date")]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(r".avatar_(\d+\.\w+)")

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y, %H:%M %p'

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

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        try:
            return datetime.strptime(
                thread_date.strip(),
                self.post_datetime_format
            )
        except:
            try:
                return dparser.parse(thread_date, dayfirst=True)
            except:
                return dateparser.parse(thread_date).replace(tzinfo=None)

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        try:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )
        except:
            try:
                return dparser.parse(thread_date, dayfirst=True)
            except:
                return dateparser.parse(post_date).replace(tzinfo=None)

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class CrackingSoulScrapper(SiteMapScrapper):

    spider_class = CrackingSoulSpider
    site_name = 'crackingsoul.com'
    site_type = 'forum'

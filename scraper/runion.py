import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
import locale
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class RUnionSpider(SitemapSpider):
    name = 'runion_spider'
    base_url = 'http://lwplxqzvmgu43uff.onion/'

    # Xpaths
    forum_xpath = '//div[@id="brdmain"]//div[@class="tclcon"]//a/@href'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_xpath = '//div[@class="blocktable"]//tr[contains(@class,"row")]'
    thread_first_page_xpath = './/div[@class="tclcon"]/div/a/@href'
    thread_last_page_xpath = './/div[@class="tclcon"]/div'\
                             '/span[@class="pagestext"]/a[last()]/@href'
    thread_date_xpath = './/td[@class="tcr"]/a/text()'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//p[@class="pagelink conl"]/strong/text()'
    post_date_xpath = '//div[@id and contains(@class, "blockpost")]'\
                      '/h2/span/a/text()'

    avatar_xpath = '//dd[@class="postavatar"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"id=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*p=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%Y-%m-%d %H ч.'
    post_datetime_format = '%Y-%m-%d %H ч.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                'proxy': PROXY
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if 'сегодня' in thread_date.lower():
            return datetime.today()
        elif "вчера" in thread_date.lower():
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

        if "сегодня" in post_date.lower():
            return datetime.today()
        elif "вчера" in post_date.lower():
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


class RUnionScrapper(SiteMapScrapper):

    spider_class = RUnionSpider
    site_name = 'runion_lwplxqzvmgu43uff'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

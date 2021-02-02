import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper



class KuketzSpider(SitemapSpider):
    name = 'kuketz_spider'
    base_url = 'https://forum.kuketz-blog.de'

    # Xpaths
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'
    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = './/div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/time/@datetime'
    pagination_xpath = '//li[@class="arrow next"]/a[@rel="next"]/@href'
    thread_pagination_xpath = '//li[@class="arrow previous"]/a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagination"]//'\
                        'li[@class="active"]/span/text()'
    post_date_xpath = '//p[@class="author"]/time/@datetime'

    avatar_xpath = '//div[@class="avatar-container"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"&t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'avatar=(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date[:-6],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        return datetime.strptime(
            post_date[:-6],
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
            # if 'f=39' not in forum_url:
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


class KuketzScrapper(SiteMapScrapper):

    spider_class = KuketzSpider
    site_name = 'forum.kuketz-blog.de'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

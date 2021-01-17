import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
import dateparser
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


class DigitalGangsterSpider(SitemapSpider):
    name = 'digitalgangster_spider'
    base_url = 'https://digitalgangster.com/7um'

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
    use_proxy = True
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = next_page.strip('.').strip()
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def get_thread_next_page(self, response):
        next_page = response.xpath(
            self.thread_pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = next_page.strip('.').strip()
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def parse_thread_url(self, thread_url):
        if thread_url:
            return thread_url.strip().strip('.')
        else:
            return

    def parse_thread_date(self, thread_date):
        thread_date = thread_date[:-6].strip()
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date[:-6].strip()
        if not post_date:
            return
        return dateparser.parse(post_date)

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url.strip('.')
            self.logger.info(forum_url)
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
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath).extract()
        for avatar_url in all_avatars:

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url.strip('.')

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )


class DigitalGangsterScrapper(SiteMapScrapper):

    spider_class = DigitalGangsterSpider
    site_name = 'digitalgangster.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

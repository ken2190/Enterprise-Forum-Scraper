import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class HackThisSiteSpider(SitemapSpider):
    name = 'hackthissite_spider'
    base_url = 'https://hackthissite.org/forums'

    # Xpaths
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'
    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = './/strong[@class="pagination"]'\
                             '/span/a[last()]/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/text()[last()]'
    pagination_xpath = '//div[@class="pagination"]/span/strong'\
                       '/following-sibling::a[1]/@href'
    thread_pagination_xpath = '//div[@class="pagination"]/span/strong'\
                              '/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//div[@class="pagination"]/span/strong/text()'
    post_date_xpath = '//p[@class="author"]/strong'\
                      '/following-sibling::text()[1]'

    avatar_xpath = '//div[@class="avatar-container"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"&t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*id=(.*)',
        re.IGNORECASE
    )

    # Other settings
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = 'on %a %b %d, %Y %I:%M %p'
    sitemap_datetime_format = 'on %a %b %d, %Y %I:%M %p'

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
            forum_url = forum_url.strip('.')
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

    def get_forum_next_page(self, response):
        next_page = response.xpath(self.pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = re.sub(r'sid=\w+', '', next_page)
        next_page = next_page.strip().strip('.')
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.thread_pagination_xpath).extract_first()
        if not next_page:
            return
        next_page = re.sub(r'sid=\w+', '', next_page)
        next_page = next_page.strip().strip('.')
        if self.base_url not in next_page:
            next_page = self.base_url + next_page
        return next_page

    def parse_thread_url(self, thread_url):
        """
        :param thread_url: str => thread url as string
        :return: str => thread url as string
        """
        if thread_url:
            thread_url = re.sub(r'sid=\w+', '', thread_url)
            return thread_url.strip().strip('.')
        else:
            return

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """
        try:
            match = self.avatar_name_pattern.findall(url)
            if '.' in match[0]:
                file_name = '{}/{}'.format(self.avatar_path, match[0])
            else:
                file_name = '{}/{}.jpg'.format(self.avatar_path, match[0])
            return file_name
        except Exception as err:
            return


class HackThisSiteScrapper(SiteMapScrapper):

    spider_class = HackThisSiteSpider
    site_name = 'hackthissite.org'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

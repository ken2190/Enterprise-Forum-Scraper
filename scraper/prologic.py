import os
import uuid
import re
import json
import scrapy
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

USER = 'vrx9'
PASS = 'Night#Pro000'

class ProLogicSpider(SitemapSpider):
    name = 'prologic_spider'
    base_url = "https://prologic.su/"

    # Xpaths
    forum_xpath = '//h4[@class="forum_name"]/strong/a/@href|'\
                  '//ol[contains(@id, "subforums_")]/li/a/@href'
    pagination_xpath = '//a[@rel="next"]/@href'
    thread_xpath = '//tr[contains(@id,"trow_")]'
    thread_first_page_xpath = './/h4/a[contains(@href,"/topic/")]/@href'
    thread_last_page_xpath = './/ul[@class="mini_pagination"]'\
                             '/li[last()]/a/@href'
    thread_date_xpath = './/li[@class="desc lighter blend_links"]/a/text()'
    thread_pagination_xpath = '//div[@class="topic_controls"]'\
                              '//a[@rel="prev"]/@href'
    thread_page_xpath = '//li[@class="page active"]/text()'
    post_date_xpath = '//div[@class="post_date"]/abbr/@title'

    avatar_xpath = '//li[@class="avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r'/topic/(\d+)-',
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = '%d %b %Y'
    post_datetime_format = '%Y-%m-%dT%H:%M:%S'

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if any(d in thread_date.lower() for d in ['сегодня', 'минут']):
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

        return datetime.strptime(
            post_date[:-6],
            self.post_datetime_format
        )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True
        )

    def parse(self, response):
        auth_key = response.xpath(
            '//input[@name="auth_key"]/@value').extract_first()
        params = {
            'auth_key': auth_key,
            'referer': 'https://prologic.su/',
            'ips_username': USER,
            'ips_password': PASS,
            "rememberMe": '1',
        }
        login_url = 'https://prologic.su/index.php?app=core&module=global'\
                    '&section=login&do=process'
        yield FormRequest(
            url=login_url,
            callback=self.parse_start,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
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


class ProLogicScrapper(SiteMapScrapper):

    spider_class = ProLogicSpider
    site_name = 'prologic.su'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [403, 406, 429, 500, 503],
            }
        )
        return settings

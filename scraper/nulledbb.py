import time
import requests
import os
import json
import re
import scrapy
import uuid
from math import ceil
from copy import deepcopy
from urllib.parse import urlencode
import configparser
from lxml.html import fromstring
from scrapy.crawler import CrawlerProcess

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scrapy import (
    Request,
    FormRequest
)


class NulledBBSpider(SitemapSpider):

    name = 'nulledbb_spider'

    # Url stuffs
    base_url = "https://nulledbb.com/"
    start_urls = ["https://nulledbb.com/"]
    sitemap_url = "https://nulledbb.com/sitemap-index.xml"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )

    # Xpath stuffs
    forum_sitemap_xpath = "//sitemap[loc[contains(text(),\"sitemap-threads.xml\")]]/loc/text()"
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/thread-\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://nulledbb.com/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1"
            }
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Loop all forum and sub forums
        forums = response.xpath(
            '//div[@class="forums-row"]//div[@class="title"]/a')
        sub_forums = response.xpath(
            '//div[@class="subforums"]//a[@title]')
        forums.extend(sub_forums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={
                    "cookiejar": uuid.uuid1().hex
                }
            )

    def parse_forum(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "next_page_url: {}".format(response.url)
        )

        threads = response.xpath(
            '//span[contains(@id, "tid_")]'
            '/a[contains(@href, "thread-")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.get_topic_id(thread_url)
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load topic id
        topic_id = response.meta.get("topic_id")

        # Save thread content
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        # Save avatar content
        avatars = response.xpath(
            '//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            file_name = '{}/{}'.format(self.avatar_path, match[0])
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
                )
            )

        # Pagination threads
        next_page = response.xpath(
            '//a[@class="pagination_next" '
            'and contains(@href, "thread-")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class NulledBBScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16
    spider_class = NulledBBSpider

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            }
        )
        return spider_settings


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

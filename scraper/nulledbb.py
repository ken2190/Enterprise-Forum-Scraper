import time
import requests
import os
import json
import re
import scrapy
from math import ceil
from copy import deepcopy
from urllib.parse import urlencode
import configparser
from scrapy.http import Request, FormRequest
from lxml.html import fromstring
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import BypassCloudfareSpider


class NulledBBSpider(BypassCloudfareSpider):
    name = 'nulledbb_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://nulledbb.com/"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://nulledbb.com'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            "user-agent": self.custom_settings.get("DEFAULT_REQUEST_HEADERS"),
            'referer': 'https://nulledbb.com/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
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
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@id, "tid_")]'
            '/a[contains(@href, "thread-")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = str(
                    int.from_bytes(
                        thread_url.encode('utf-8'), byteorder='big'
                    ) % (10 ** 7)
                )
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

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
                meta={
                    'file_name': file_name,
                }
            )

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
                meta={'topic_id': topic_id}
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class NulledBBScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 16
        self.ensure_avatar_path()

    def ensure_avatar_path(self, ):
        self.avatar_path = f'{self.output_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def do_scrape(self):
        settings = {
            "DOWNLOADER_MIDDLEWARES": {
                'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            },
            'DOWNLOAD_DELAY': self.request_delay,
            'CONCURRENT_REQUESTS': self.no_of_threads,
            'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            'RETRY_HTTP_CODES': [403, 429, 500, 503],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

        }
        process = CrawlerProcess(settings)
        process.crawl(NulledBBSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

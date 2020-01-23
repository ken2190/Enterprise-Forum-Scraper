import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
import hashlib
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import SiteMapScrapper

USER = 'Cyrax_011'
PASS = 'Night#India065'

PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'


class EnvoySpider(scrapy.Spider):
    name = 'envoy_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'http://envoys5appps3bin.onion/index.php'
        self.topic_pattern = re.compile(r'topic=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'topic=\d+\.(\d+)')
        self.output_path = kwargs.get("output_path")
        self.avatar_path = kwargs.get("avatar_path")
        self.proxy = kwargs.get("proxy") or PROXY
        self.headers = {
            'Accept': 'text/html,application/xhtml+xm…plication/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'envoys5appps3bin.onion',
            'Referer': 'http://envoys5appps3bin.onion/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': USER_AGENT,
        }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.process_login,
            meta={'proxy': self.proxy}
        )

    def process_login(self, response):
        token = response.xpath(
            '//p[@class="centertext smalltext"]/'
            'following-sibling::input[1]'
        )
        if not token:
            return
        token_key = token[0].xpath('@name').extract_first()
        token_value = token[0].xpath('@value').extract_first()
        form_data = {
            "cookieneverexp": "on",
            "hash_passwrd": "",
            "passwrd": PASS,
            "user": USER,
            token_key: token_value,
        }
        login_url = f'{self.base_url}?action=login2'
        yield FormRequest(
            url=login_url,
            headers=self.headers,
            formdata=form_data,
            callback=self.parse_main_page,
            meta={'proxy': self.proxy},
            dont_filter=True,
        )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//a[contains(@href, "index.php?board=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            url = url.strip('/')
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
            )

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//td[contains(@class, "subject ")]'
            '//span[contains(@id, "msg_")]/a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={
                    'topic_id': topic_id[0],
                    'proxy': self.proxy
                },
            )

        next_page = response.xpath('//div[@class="pagelinks floatleft"]/strong'
                                   '/following-sibling::a[1]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(int(pagination[0])/15 + 1)
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//li[@class="avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url:
                continue
            avatar_url = self.base_url + avatar_url\
                if not avatar_url.startswith('http') else avatar_url
            user_id = self.avatar_name_pattern.findall(avatar_url)
            if not user_id:
                continue
            file_name = '{}/{}'.format(self.avatar_path, user_id[0])
            if os.path.exists(file_name):
                continue
            headers = None if 'linx.li' in avatar_url else self.headers

            yield Request(
                url=avatar_url,
                headers=headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'proxy': self.proxy
                }
            )

        next_page = response.xpath('//div[@class="pagelinks floatleft"]/strong'
                                   '/following-sibling::a[1]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={
                    'topic_id': topic_id,
                    'proxy': self.proxy
                }
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class EnvoyScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16

    spider_class = EnvoySpider

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )

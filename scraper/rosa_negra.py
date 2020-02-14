import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
import hashlib
from scrapy.http import Request, FormRequest
from scraper.base_scrapper import SiteMapScrapper

USER = 'Cyrax011'
PASS = 'Night#India065'

REQUEST_DELAY = 0.5
NO_OF_THREADS = 16

PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'


class RosaNegraSpider(scrapy.Spider):
    name = 'rosanegra_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'http://3pc3yapw2xmsfnfx.onion'
        self.login_url = 'http://3pc3yapw2xmsfnfx.onion/ucp.php?mode=login'
        self.topic_pattern = re.compile(r't=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*=(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'start=(\d+)')
        self.output_path = kwargs.get("output_path")
        self.useronly = kwargs.get("useronly")
        self.avatar_path = kwargs.get("avatar_path")
        self.start_date = kwargs.get("start_date")
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': self.base_url,
            'User-Agent': USER_AGENT,
        }

    def start_requests(self):
        form_data = {
            'username': USER,
            'password': PASS,
            'autologin': 'on',
            'login': 'Entrar',
            'redirect': './index.php?',
        }
        yield FormRequest(
            url=self.login_url,
            formdata=form_data,
            callback=self.parse_main_page,
            meta={'proxy': PROXY},
            dont_filter=True,
        )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//a[contains(@href, "viewforum.php?f=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            url = url.strip('.')
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                callback=self.parse_forum,
                meta={'proxy': PROXY}
            )

    def parse_forum(self, response):
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//div[@class="list-inner"]'
            '/a[contains(@href,"./viewtopic.php?f=")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            thread_url = thread_url.strip('.')
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
                callback=self.parse_thread,
                meta={
                    'topic_id': topic_id[0],
                    'proxy': PROXY
                },
            )

        next_page = response.xpath(
            '//li[@class="arrow next"]/a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            next_page_url = next_page_url.strip('.')
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                meta={'proxy': PROXY}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(int(pagination[0])/20 + 1)
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//div[@class="avatar-container"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            avatar_url = avatar_url.strip('.')
            if not avatar_url:
                continue
            avatar_url = self.base_url + avatar_url\
                if not avatar_url.startswith('http') else avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            file_name = '{}/{}'.format(self.avatar_path, match[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'proxy': PROXY
                }
            )

        next_page = response.xpath(
            '//li[@class="arrow next"]/a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            next_page_url = next_page_url.strip('.')
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                meta={
                    'topic_id': topic_id,
                    'proxy': PROXY
                }
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class RosaNegraScrapper(SiteMapScrapper):

    spider_class = RosaNegraSpider
    site_name = 'Rosa Negra (3pc3yapw2xmsfnfx.onion)'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS
            }
        )
        return spider_settings

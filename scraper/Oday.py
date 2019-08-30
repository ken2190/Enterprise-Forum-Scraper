import os
import json
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


USER = "cetus"
PASS = "Night-0day#1"
PROXY = 'http://127.0.0.1:8118'


class OdaySpider(scrapy.Spider):
    name = 'oday_spider'

    def __init__(self, output_path, avatar_path, proxy):
        self.start_url = self.base_url = "http://qzbkwswfv5k2oj5d.onion/"
        self.proxy = proxy
        self.topic_pattern = re.compile(r'.*thread-(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'-page-(\d+)')
        self.username_pattern = re.compile(r'user-(\d+)')
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Host': 'qzbkwswfv5k2oj5d.onion',
            'Referer': 'http://qzbkwswfv5k2oj5d.onion',
        }
        self.set_users_path()

    def set_users_path(self, ):
        self.user_path = os.path.join(self.output_path, 'users')
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def start_requests(self):
        formdata = {
            'action': 'do_login',
            'password': PASS,
            'url': '/index.php',
            'username': USER,
        }
        login_url = 'http://qzbkwswfv5k2oj5d.onion/member.php'
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=formdata,
            headers=self.headers,
            meta={'proxy': self.proxy}
        )

    def parse(self, response):
        forums = response.xpath(
            '//td[(@class="trow1" or @class="trow2") and '
            '@valign="top"]//a[contains(@href, "forum-")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

        # Test for single Forum
        # url = 'http://qzbkwswfv5k2oj5d.onion/forum-49.html'
        # yield Request(
        #     url=url,
        #     callback=self.parse_forum,
        #     headers=self.headers,
        #     meta={'proxy': self.proxy}
        # )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[contains(@id, "tid_")]')
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
                callback=self.parse_thread,
                headers=self.headers,
                meta={'topic_id': topic_id[0], 'proxy': self.proxy}
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(pagination[0])
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//span[@class="smalltext"]/a')
        for avatar in avatars:
            avatar_url = avatar.xpath('img/@src').extract_first()
            if not avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url.strip('.')
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
                    'proxy': self.proxy
                }
            )

        users = response.xpath('//span[@class="largetext"]/a')
        for user in users:
            user_url = user.xpath('@href').extract_first()
            if self.base_url not in user_url:
                user_url = self.base_url + user_url
            user_id = self.username_pattern.findall(user_url)
            if not user_id:
                continue
            file_name = '{}/{}.html'.format(self.user_path, user_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=user_url,
                headers=self.headers,
                callback=self.parse_user,
                meta={
                    'file_name': file_name,
                    'user_id': user_id[0],
                    'proxy': self.proxy,
                }
            )

        next_page = response.xpath(
            '//div[@class="pagination"]/a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                headers=self.headers,
                meta={'topic_id': topic_id, 'proxy': self.proxy}
            )

    def parse_user(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"User {response.meta['user_id']} done..!")

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class OdayScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or PROXY
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
                'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None
            },
            'DOWNLOAD_DELAY': self.request_delay,
            'CONCURRENT_REQUESTS': self.no_of_threads,
            'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            'RETRY_HTTP_CODES': [403, 429, 500, 503],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

        }
        process = CrawlerProcess(settings)
        process.crawl(OdaySpider, self.output_path, self.avatar_path, self.proxy)
        process.start()

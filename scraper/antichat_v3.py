import sys
import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import BypassCloudfareSpider


USER = 'blacklotus2000@protonmail.com'
PASS = 'Night#Anti999'


class AntichatSpider(BypassCloudfareSpider):
    name = 'antichat_spider'

    def __init__(self, output_path):
        self.base_url = 'https://forum.antichat.ru/'
        self.topic_pattern = re.compile(r'/threads/(\d+)/')
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.pagination_pattern = re.compile(r'page-(\d+)')
        self.cloudfare_error = None
        self.output_path = output_path
        self.headers = {
            'origin': 'https://forum.antichat.ru',
            'referer': 'https://forum.antichat.ru/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': self.custom_settings.get("DEFAULT_REQUEST_HEADERS")
        }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            callback=self.parse,
            headers=self.headers,
        )

    def proceed_for_login(self):
        login_url = 'https://forum.antichat.ru/login/login'
        params = {
            'login': USER,
            'password': PASS,
            'register': '0',
            "remember": '1',
            'cookie_check': '1',
            'redirect': 'https://forum.antichat.ru/',
            '_xfToken': ''
        }
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse(self, response):
        forums = response.xpath(
            '//div[@class="nodelistBlock nodeText"]'
            '/h3[@class="nodeTitle"]/a')
        subforums = response.xpath(
            '//ol[@class="subForumList"]'
            '//h4[@class="nodeTitle"]/a')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = f'{self.base_url}{url}'

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
            )

    def parse_forum(self, response):
        topic_blocks = response.xpath(
            '//ol[@class="discussionListItems"]/li[@id]')
        if not topic_blocks:
            topic_blocks = response.xpath(
                '//div[@class="uix_stickyThreads"]/li')
        for topic in topic_blocks:
            thread_url = topic.xpath(
                'div//h3[@class="title"]/a[@data-previewurl]/'
                '@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = f'{self.base_url}{thread_url}'
            match = self.topic_pattern.findall(thread_url)
            if not match:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, match[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': match[0]}
            )
        next_page = response.xpath(
            '//a[@class="text" and text()="Next >"]'
            )
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            # f.write(response.text.encode('cp1252'))
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        next_page = response.xpath(
            '//a[@class="text" and text()="Next >"]'
            )
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


class Antichatv3Scrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 10

    def do_scrape(self):
        settings = {
            "DOWNLOADER_MIDDLEWARES": {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
                'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
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
        if self.proxy:
            settings['DOWNLOADER_MIDDLEWARES'].update({
                'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
                'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
                'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
            })
            settings.update({
                'ROTATING_PROXY_LIST': self.proxy,

            })
        process = CrawlerProcess(settings)
        process.crawl(AntichatSpider, self.output_path)
        process.start()

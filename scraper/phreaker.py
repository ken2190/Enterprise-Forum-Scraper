import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from urllib.parse import urlencode
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

USER = 'thecreator101@protonmail.com'
PASS = 'Night#Phreaker'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'


class PhreakerSpider(scrapy.Spider):
    name = 'phreaker_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://phreaker.pro"
        self.topic_pattern = re.compile(r'/threads/.*\.(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.start_url = 'https://phreaker.pro'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            "user-agent": USER_AGENT,
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.get_token
        )

    def get_token(self, response):
        match = re.findall(r'csrf: \'(.*?)\'', response.text)
        params = {
            '_xfRequestUri': '/forum/',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        token_url = 'https://phreaker.pro/forum/login/?' + urlencode(params)
        yield Request(
            url=token_url,
            headers=self.headers,
            callback=self.proceed_for_login
        )

    def proceed_for_login(self, response):
        json_response = json.loads(response.text)
        html_response = fromstring(json_response['html']['content'])
        token = html_response.xpath(
            '//input[@name="_xfToken"]/@value')[0]
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': 'https://phreaker.pro/forum',
            '_xfToken': token
        }
        yield FormRequest(
            url="https://phreaker.pro/forum/login/login",
            callback=self.parse_main_page,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
            )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//h3[@class="node-title"]/a')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if not url.endswith('.48/'):
            #     continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@data-preview-url]')
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
                meta={'topic_id': topic_id[0]}
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
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

        avatars = response.xpath('//a[@class="avatar avatar--m"]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            user_id = avatar.xpath('@alt').re(r'(\w+)')
            if not user_id:
                continue
            file_name = '{}/{}.jpg'.format(self.avatar_path, user_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'user_id': user_id[0]
                }
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
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
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")


class PhreakerScrapper():
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
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
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
        process.crawl(PhreakerSpider, self.output_path, self.avatar_path)
        process.start()

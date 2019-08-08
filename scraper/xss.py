import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

USER = 'cyrax'
PASS = 'Night#Xss007'


class XSSSpider(scrapy.Spider):
    name = 'xss_spider'

    def __init__(self, output_path):
        self.base_url = "https://xss.is"
        self.start_url = '{}/forums/'.format(self.base_url)
        self.topic_pattern = re.compile(r'threads/(\d+)/$')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.start_url = 'https://xss.is/'
        self.output_path = output_path
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/76.0.3809.87 Safari/537.36",
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': 'https://xss.is/',
            '_xfToken': token
        }
        yield FormRequest(
            url="https://xss.is/login/login",
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


class XSSScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 16

    def do_scrape(self):
        settings = {
            'DOWNLOAD_DELAY': self.request_delay,
            'CONCURRENT_REQUESTS': self.no_of_threads,
            'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            'RETRY_HTTP_CODES': [429, 500, 503],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,
            'HTTPERROR_ALLOWED_CODES': [403],

        }
        if self.proxy:
            settings.update({
                "DOWNLOADER_MIDDLEWARES": {
                    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
                    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
                    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
                    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
                    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
                },
                'ROTATING_PROXY_LIST': self.proxy,

            })
        process = CrawlerProcess(settings)
        process.crawl(XSSSpider, self.output_path)
        process.start()

if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

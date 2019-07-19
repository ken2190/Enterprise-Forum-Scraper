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


USER = 'sandman'
PASS = 'Sand#LCP001'
CODE = 'shithead'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) "\
             "AppleWebKit/537.36 (KHTML, like Gecko) "\
             "Chrome/75.0.3770.142 Safari/537.36"


class LCPSpider(scrapy.Spider):
    name = 'lcp_spider'

    def __init__(self, output_path):
        self.base_url = "https://lcp.cc/"
        self.start_url = '{}/forums/'.format(self.base_url)
        self.topic_pattern = re.compile(r'viewe=(\w+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.start_url = 'https://lcp.cc/login.php'
        self.output_path = output_path
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        action_url = response.xpath(
            '//form[@method="post"]/@action').extract_first()
        if self.base_url not in action_url:
            action_url = self.base_url + action_url
        code_block = response.xpath(
            '//td[input[@name="m"]]/'
            'preceding-sibling::td[1]/font/text()').extract_first()
        code_number = code_block.replace('M', '')
        code = ''
        for c in code_number:
            code += CODE[int(c) - 1]
        formdata = {
            'l': USER,
            'p': PASS,
            'm': code
        }
        yield FormRequest(
            url=action_url,
            callback=self.parse_main_page,
            formdata=formdata,
            headers=self.headers
            )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//a[contains(@href, "index.php?show")]')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            "Connection": 'keep-alive',
            'Host': 'lcp.cc',
            'Referer': response.url,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': USER_AGENT
        }
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = f'{self.base_url}forum/{url}'

            yield Request(
                url=url,
                headers=headers,
                callback=self.parse_forum,
                meta={'headers': headers}
            )

    def parse_forum(self, response):
        old_pages = response.xpath(
            '//a[text()="Show Old Pages"]/@href').extract_first()
        if old_pages:
            url = f'{self.base_url}forum/{old_pages}'
            yield Request(
                url=url,
                headers=response.meta['headers'],
                callback=self.parse_forum
            )
        else:
            threads = response.xpath(
                '//a[contains(@href, "viewe=")]')
            max_pages = 10
            counter = 0
            for thread in threads:
                thread_url = thread.xpath('@href').extract_first().strip('.')
                if self.base_url not in thread_url:
                    thread_url = f'{self.base_url}forum/{thread_url}'
                match = self.topic_pattern.findall(thread_url)
                if not match:
                    continue
                topic_id = str(
                    int.from_bytes(
                        match[0].encode('utf-8'), byteorder='big'
                    ) % (10 ** 7)
                )
                file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
                if os.path.exists(file_name):
                    continue
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;'
                              'q=0.9,image/webp,image/apng,*/*;'
                              'q=0.8,application/signed-exchange;v=b3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                    "Connection": 'keep-alive',
                    'Host': 'lcp.cc',
                    'Referer': response.url,
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': USER_AGENT
                }
                yield Request(
                    url=thread_url,
                    headers=headers,
                    callback=self.parse_thread,
                    meta={'topic_id': topic_id}
                )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('cp1252'))
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


class LCPScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 20

    def do_scrape(self):
        settings = {
            'DOWNLOAD_DELAY': self.request_delay,
            'CONCURRENT_REQUESTS': self.no_of_threads,
            'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            'RETRY_HTTP_CODES': [403, 429, 500, 503],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

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
        process.crawl(LCPSpider, self.output_path)
        process.start()

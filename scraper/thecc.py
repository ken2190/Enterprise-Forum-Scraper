import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


class TheCCSpider(scrapy.Spider):
    name = 'thecc_spider'

    def __init__(self, output_path):
        self.topic_pattern = re.compile(r'.*\.(\d+)/$')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.start_url = 'https://thecc.bz/'
        self.output_path = output_path
        self.pagination_pattern = re.compile(r'/(\d+)/$')
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/74.0.3729.169 Safari/537.36",
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        # print(response.text)
        forums = response.xpath(
            '//a[@class="subject"]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//td[contains(@class, "subject ")]//span/a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
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

        next_page = response.xpath('//a[class="navPages"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
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
            print(f'{topic_id}-1 done..!')

        next_page = response.xpath('//a[class="navPages"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )


class TheCCScrapper():
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
        process.crawl(TheCCSpider, self.output_path)
        process.start()

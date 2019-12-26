import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import BypassCloudfareSpider


REQUEST_DELAY = 0.1
NO_OF_THREADS = 20


class CanadaHQSpider(BypassCloudfareSpider):
    name = 'canadahq_spider'

    def __init__(self, output_path, user_path, avatar_path):
        self.base_url = 'https://canadahq.at/'
        self.topic_pattern = re.compile(r't=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://canadahq.at/home'
        self.output_path = output_path
        self.user_path = user_path
        self.avatar_path = avatar_path
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'referer': 'https://fuckav.ru/',
            'user-agent': self.custom_settings.get("DEFAULT_REQUEST_HEADERS"),
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="menu-content"]/ul/li/a')
        for url in urls:
            url = url.xpath('@href').extract_first()
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_results
            )

    def parse_results(self, response):
        print('next_page_url: {}'.format(response.url))
        products = response.xpath(
            '//a[@class="product"]')
        for product in products:
            product_url = product.xpath('@href').extract_first()
            if self.base_url not in product_url:
                product_url = self.base_url + product_url
            file_id = product_url.rsplit('/', 1)[-1]
            file_name = '{}/{}.html'.format(self.output_path, file_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=product_url,
                headers=self.headers,
                callback=self.parse_product,
                meta={'file_id': file_id}
            )

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_results
            )

    def parse_product(self, response):
        file_id = response.meta['file_id']
        file_name = '{}/{}.html'.format(self.output_path, file_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'Product: {file_id} done..!')

        user_url = response.xpath(
            '//a[contains(text(), "profile") and contains(text(), "View")]'
            '/@href').extract_first()
        if not user_url:
            return
        user_id = user_url.rsplit('/', 1)[-1]
        file_name = '{}/{}.html'.format(self.user_path, user_id)
        if os.path.exists(file_name):
            return
        yield Request(
            url=user_url,
            headers=self.headers,
            callback=self.parse_user,
            meta={
                'file_name': file_name,
                'user_id': user_id
            }
        )

    def parse_user(self, response):
        user_id = response.meta['user_id']
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'User: {user_id} done..!')

        avatar_url = response.xpath(
            '//img[@class="img-responsive"]/@src').extract_first()
        if not avatar_url:
            return
        ext = avatar_url.rsplit('.', 1)[-1]
        if not ext:
            ext = 'jpg'
        file_name = '{}/{}.{}'.format(self.avatar_path, user_id, ext)
        if os.path.exists(file_name):
            return
        yield Request(
            url=avatar_url,
            headers=self.headers,
            callback=self.parse_avatar,
            meta={
                'file_name': file_name,
                'user_id': user_id
            }
        )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")


class CanadaHQScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.ensure_users_path()

    def ensure_users_path(self, ):
        self.user_path = f'{self.output_path}/users'
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

        self.avatar_path = f'{self.user_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def do_scrape(self):
        settings = {
            "DOWNLOADER_MIDDLEWARES": {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
                'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
                'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
                'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None
            },
            'DOWNLOAD_DELAY': REQUEST_DELAY,
            'CONCURRENT_REQUESTS': NO_OF_THREADS,
            'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
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
        process.crawl(
            CanadaHQSpider, self.output_path,
            self.user_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

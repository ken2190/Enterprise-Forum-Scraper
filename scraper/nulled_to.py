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


COOKIE = '__cfduid=d0eb09d1f4371aac293f1edb40345df281550158324; PHPSESSID=6vf9gf9ibkeftbnm3aapfqn315; _ga=GA1.2.1983188853.1567315364; nulledmodtids=%2C; nulledsession_id=a25e4f5f4132eb2b5e4c8c7c2dfbd283; _gid=GA1.2.124956148.1567574844; cf_clearance=2693a92a6669c24bd0c03cdf20f64c0b7b2f812d-1567582882-86400-150'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
USER = 'Cyrax_011'
PASS = 'Night#India065'


class NulledSpider(scrapy.Spider):
    name = 'nulled_spider'

    def __init__(self, output_path, avatar_path=None, urlsonly=None):
        self.base_url = "https://www.nulled.to"
        self.topic_pattern = re.compile(r'topic/(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')
        self.start_url = 'https://www.nulled.to'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.urlsonly = urlsonly
        self.headers = {
            'user-agent': USER_AGENT,
            'cookie': COOKIE,
            'referer': 'https://www.nulled.to/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
        }

    def start_requests(self):
        # Proceed for banlist
        if not self.avatar_path:
            ban_url = 'https://www.nulled.to/ban-list.php'
            yield Request(
                url=ban_url,
                headers=self.headers,
                callback=self.parse_ban_list,
                meta={'pagination': 1}
            )
        elif self.urlsonly:
            self.output_url_file = open(self.output_path + '/urls.txt', 'w')
            yield Request(
                url=self.start_url,
                headers=self.headers,
                callback=self.parse
            )
        else:
            input_file = self.output_path + '/urls.txt'
            if not os.path.exists(input_file):
                print('URL File not found. Exiting!!')
                return
            for thread_url in open(input_file, 'r'):
                thread_url = thread_url.strip()
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

    def parse_ban_list(self, response):
        pagination = response.meta['pagination']
        file_name = '{}/page-{}.html'.format(
            self.output_path, pagination)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'page-{pagination} done..!')
        last_page = response.xpath('//li[@class="last"]/a')
        if last_page and pagination == 1:
            last_page_index = last_page.xpath('@href').re(r'st=(\d+)')
            for st in range(50, int(last_page_index[0]) + 50, 50):
                url = f'https://www.nulled.to/ban-list.php?&st={st}'
                pagination += 1
                yield Request(
                    url=url,
                    headers=self.headers,
                    callback=self.parse_ban_list,
                    meta={'pagination': pagination}
                )

    def parse(self, response):
        forums = response.xpath(
            '//h4[@class="forum_name"]/strong/a')
        sub_forums = response.xpath(
            '//li/i[@class="fa fa-folder"]'
            '/following-sibling::a[1]')
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
            '//a[@itemprop="url" and contains(@id, "tid-link-")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            self.output_url_file.write(thread_url)
            self.output_url_file.write('\n')

        next_page = response.xpath('//li[@class="next"]/a')
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
            '//li[@class="avatar"]/img')
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

        next_page = response.xpath('//li[@class="next"]/a')
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


class NulledToScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 16
        self.urlsonly = kwargs.get('urlsonly')
        self.banlist_path = None
        self.avatar_path = None
        if kwargs.get('banlist'):
            self.ensure_ban_path()
        else:
            self.ensure_avatar_path()

    def ensure_ban_path(self, ):
        self.banlist_path = f'{self.output_path}/banlist'
        if not os.path.exists(self.banlist_path):
            os.makedirs(self.banlist_path)

    def ensure_avatar_path(self, ):
        self.avatar_path = f'{self.output_path}/avatars'
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
            'DOWNLOAD_DELAY': self.request_delay,
            'CONCURRENT_REQUESTS': self.no_of_threads,
            'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

        }
        process = CrawlerProcess(settings)
        if self.banlist_path:
            process.crawl(
                NulledSpider, self.banlist_path,
            )
        else:
            process.crawl(
                NulledSpider, self.output_path,
                self.avatar_path, self.urlsonly
            )
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

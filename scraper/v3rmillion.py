import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

COOKIE = '__cfduid=db30372c5cfd52f51055e2f827e39b6941559539109; _ga=GA1.2.73025486.1559539374; mybb[lastvisit]=1559540977; coppadob=11-4-1986; mybb[lastactive]=1564478511; mybbuser=1271838_fnY3vEdoam10xfLfL3lNJhuFbw6D5G0eCRxhE4wLtZA2FQdwRb; loginattempts=1; identifier=v3rm5d400e37ba2a1; cf_clearance=aeb0e67513fac0aa094f969103cd7687dc6215a1-1567491640-14400-250; sid=4306ec1d599dae4c253ad2ac674ad7b1; _gid=GA1.2.1297305583.1567491642'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
REQUEST_DELAY = 0.75
NO_OF_THREADS = 5


class V3RMillionSpider(scrapy.Spider):
    name = 'v3rmillion_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = 'https://v3rmillion.net/'
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://v3rmillion.net/'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'referer': 'https://v3rmillion.net/',
            'user-agent': USER_AGENT,
            'cookie': COOKIE,
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        forums = response.xpath(
            '//td[@class="trow1" or @class="trow2"]/strong'
            '/a[contains(@href, "forumdisplay.php?fid=")]')
        subforums = response.xpath(
            '//span[@class="sub_control"]'
            '/a[contains(@href, "forumdisplay.php?fid=")]')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            if 'fid=21' not in url:
                continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@id, "tid_")]'
            '/a[contains(@href, "showthread.php?tid=")]')
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

        next_page = response.xpath('//a[@class="pagination_next"]')
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

        avatars = response.xpath('//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
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

        next_page = response.xpath(
            '//div[@class="pagination"]'
            '/a[@class="pagination_next"]')
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


class V3RMillionScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.ensure_avatar_path()

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
        process.crawl(V3RMillionSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

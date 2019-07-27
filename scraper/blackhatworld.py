import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


class BlackHatWorldSpider(scrapy.Spider):
    name = 'blackhatworld_spider'

    def __init__(self, output_path):
        self.base_url = "https://www.blackhatworld.com/"
        self.start_url = '{}/forums/'.format(self.base_url)
        self.topic_pattern = re.compile(r'.*\.(\d+)/$')
        self.pagination_pattern = re.compile(r'.*page-(\d+)$')
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.username_pattern = re.compile(r'members/(.*)\.\d+')
        self.start_url = 'https://www.blackhatworld.com/forums/'
        self.output_path = output_path
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/74.0.3729.169 Safari/537.36",
        }
        self.set_users_path()
        self.ensure_avatar_path()

    def set_users_path(self, ):
        self.user_path = os.path.join(self.output_path, 'users')
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def ensure_avatar_path(self):
        self.avatar_path = f'{self.output_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        # print(response.text)
        forums = response.xpath(
            '//ol[@class="nodeList"]//h3[@class="nodeTitle"]/a')
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
            '//li[contains(@id, "thread-")]//h3[@class="title"]/a')
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

        users = response.xpath('//span[@class="avatarContainer"]/a')
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
                # headers=self.headers,
                callback=self.parse_user,
                meta={
                    'file_name': file_name,
                    'user_id': user_id[0]
                }
            )

        next_page = response.xpath('//a[text()="Next >"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_user(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"User {response.meta['user_id']} done..!")

        avatar_url = response.xpath(
            '//img[@itemprop="photo"]/@src').extract_first()
        name_match = self.avatar_name_pattern.findall(avatar_url)
        if not name_match:
            return
        name = name_match[0]
        file_name = '{}/{}'.format(self.avatar_path, name)
        if os.path.exists(file_name):
            return
        yield Request(
            url=avatar_url,
            # headers=self.headers,
            callback=self.parse_avatar,
            meta={
                'file_name': file_name,
                'user_id': response.meta['user_id']
            }
        )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-1 done..!')

        next_page = response.xpath('//a[text()="Next >"]')
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


class BlackHatWorldScrapper():
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
        process.crawl(BlackHatWorldSpider, self.output_path)
        process.start()

if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

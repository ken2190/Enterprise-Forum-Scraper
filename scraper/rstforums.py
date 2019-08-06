import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


class RSTForumsSpider(scrapy.Spider):
    name = 'rstforums_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://rstforums.com/"
        self.topic_pattern = re.compile(r'topic/(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*/page/(\d+)/')
        self.start_url = 'https://rstforums.com/forum/'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/75.0.3770.142 Safari/537.36",
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        forums = response.xpath(
            '//div[@class="ipsDataItem_main"]//h4/a')
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
            '//div[@class="ipsDataItem_main"]/h4//a')
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

        next_page = response.xpath('//li[@class="ipsPagination_next"]/a')
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

        avatars = response.xpath('//li[@class="cAuthorPane_photo"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if 'image/svg' in avatar_url:
                continue
            user_id = avatar.xpath('@alt').extract_first()
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
                    'user_id': user_id
                }
            )

        next_page = response.xpath('//li[@class="ipsPagination_next"]/a')
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


class RSTForumsScrapper():
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
        process.crawl(RSTForumsSpider, self.output_path, self.avatar_path)
        process.start()

if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

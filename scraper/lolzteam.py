import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

USER = "darkcylon1@protonmail.com"
PASS = "Night#Kgg2"
COOKIE = '_ym_uid=1567310450846594086; _ym_d=1567310450; G_ENABLED_IDPS=google; xf_user=382549%2C854191992b95fa6bb89faab3ebf427810b08fe5f; xf_logged_in=1; xf_id=44e73a4e69648fe3add69b0c046c0e6a; xf_session=ec00815c2dc963355cd795f8c7dbcf94; _ym_isad=1; _ym_visorc_51992225=w'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'


class LolzSpider(scrapy.Spider):
    name = 'lolz_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://lolzteam.net/"
        self.topic_pattern = re.compile(r'threads/(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,hi;q=0.8",
            "content-type": "content-type: application/x-www-form-urlencoded",
            "origin": "https://lolzteam.net",
            "referer": "https://lolzteam.net",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "cookie": COOKIE,
            'if-modified-since': 'Sun, 01 Sep 2019 01:58:13 GMT',
            "user-agent": USER_AGENT
        }

    def start_requests(self):
        data = {
            "login": USER,
            "password": PASS,
            "remember": "1",
            "stopfuckingbrute1337": "1",
            "cookie_check": "1",
            "_xfToken": "",
            "redirect": "https://lolzteam.net"
        }
        login_url = 'https://lolzteam.net/login/login'
        yield Request(
            url=self.base_url,
            headers=self.headers,
        )

    def parse(self, response):
        forums = response.xpath(
            '//ol[@class="nodeList"]//h3[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        subforums = response.xpath(
            '//ol[@class="nodeList"]//h4[@class="nodeTitle"]'
            '/a[contains(@href, "forums/")]')
        forums.extend(subforums)
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
            '//div[@class="discussionListItem--Wrapper"]'
            '/a[contains(@href, "")]')
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

        next_page_url = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href').extract_first()
        if next_page_url:
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
            '//div[@class="avatarHolder"]/a/span[@style and @class]')
        for avatar in avatars:
            avatar_url = avatar.xpath('@style').re(r'url\(\'(.*?)\'\)')
            if not avatar_url:
                continue
            if self.base_url not in avatar_url[0]:
                avatar_url = self.base_url + avatar_url[0]
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

        next_page_url = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]/@href').extract_first()
        if next_page_url:
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


class LolzScrapper():
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
        process.crawl(LolzSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

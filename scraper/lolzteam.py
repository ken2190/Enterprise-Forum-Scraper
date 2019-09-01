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
COOKIE = 'G_ENABLED_IDPS=google; _ym_uid=1567302698765321515; _ym_d=1567302698; _ym_isad=1; _ym_visorc_51992225=w; xf_id=712c5ffd68383395d1997185552c8e02; xf_user=382549%2C854191992b95fa6bb89faab3ebf427810b08fe5f; xf_logged_in=1; xf_session=0dcb35f09fe9ff8ea45e63136704202e'
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'

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
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
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
            '//ol[@class="nodeList"]//h3[@class="nodeTitle"]/a[contains(@href, "forums/")]')
        subforums = response.xpath(
            '//ol[@class="nodeList"]//h4[@class="nodeTitle"]/a[contains(@href, "forums/")]')
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

        next_page = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]')
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

        next_page = response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::a[1]')
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
                'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
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

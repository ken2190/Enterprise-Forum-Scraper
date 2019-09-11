import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
import hashlib
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


CODE = 'shithead'
USER = "Sandman011"
PASS = '12312312232312111'

PROXY = 'http://127.0.0.1:8118'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0'


class KorovkaSpider(scrapy.Spider):
    name = 'korovka_spider'

    def __init__(self, output_path, avatar_path, proxy):
        self.base_url = "http://korovka32xc3t5cg.onion/"
        self.topic_pattern = re.compile(r't=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.proxy = proxy
        self.headers = {
            'Accept': 'text/html,application/xhtml+xm…plication/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'korovka32xc3t5cg.onion',
            'Referer': 'http://korovka32xc3t5cg.onion/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': USER_AGENT,
        }

    def start_requests(self):
        md5_pass = hashlib.md5(PASS.encode('utf-8')).hexdigest()
        login_url = 'http://korovka32xc3t5cg.onion/login.php?do=login'
        formdata = {
            'cookieuser': '1',
            'do': 'login',
            'url': '/',
            'vb_login_md5password': md5_pass,
            'vb_login_md5password_utf': md5_pass,
            'vb_login_password': '',
            'vb_login_username': USER
        }
        yield FormRequest(
            url=login_url,
            formdata=formdata,
            headers=self.headers,
            callback=self.after_login,
            meta={'proxy': self.proxy}
        )

    def after_login(self, response):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_code,
            meta={'proxy': self.proxy}
        )

    def parse_code(self, response):
        code_block = response.xpath(
            '//td[contains(text(), "буквы Вашего кодового слова форму")]'
            '/text()').re(r'Введите (\d+)-.*? и (\d+)')
        security_token = response.xpath(
            '//input[@name="securitytoken"]/@value').extract_first()
        s = response.xpath(
            '//input[@name="s"]/@value').extract_first()
        code = ''
        for c in code_block:
            code += CODE[int(c) - 1]
        formdata = {
            'apa_authcode': code,
            's': s,
            'securitytoken': security_token
        }
        code_submit_url = 'http://korovka32xc3t5cg.onion/misc.php?do=apa&check=1'
        yield FormRequest(
            url=code_submit_url,
            callback=self.parse_main_page,
            formdata=formdata,
            headers=self.headers,
            meta={'proxy': self.proxy}
        )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?f=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            url = url.strip('/')
            if self.base_url not in url:
                url = self.base_url + url

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//td[contains(@id, "td_threadtitle_")]'
            '/div/a[contains(@href, "showthread.php?t=")]')
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
                meta={
                    'topic_id': topic_id[0],
                    'proxy': self.proxy
                },
            )

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
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

        avatars = response.xpath('//a[contains(@href, "member.php?u=")]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            user_id = avatar.xpath('@alt').extract_first()
            if not user_id:
                continue
            file_name = '{}/{}.jpg'.format(self.avatar_path, user_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'user_id': user_id,
                    'proxy': self.proxy
                }
            )

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={
                    'topic_id': topic_id,
                    'proxy': self.proxy
                }
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")


class KorovkaScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or PROXY
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
        process = CrawlerProcess(settings)
        process.crawl(KorovkaSpider, self.output_path, self.avatar_path, self.proxy)
        process.start()

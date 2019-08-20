import time
import requests
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


COOKIE = '__cfduid=d08235920bb81ba0a497cd279c18a86721566270081; cf_clearance=650b9a413b9b8010e93b1de2f24b9fd21a7c0c84-1566270084-604800-250; mybb[lastvisit]=1566270084; mybb[lastactive]=1566270108; _ga=GA1.2.421571632.1566270085; _gid=GA1.2.1014853299.1566270085; loginattempts=1; mybbuser=4353313_cUau1qFER8nWSNHD5Br9LEz37EATcPO1Ziwd0DIOcvJ8zNzRsJ; myalerts=MTg5NTEzMzQwNzU5Njk%3D; mybb[gdpr]=1; sid=9e1487847fd780084732cd4129379709; menutabs=0; _gat_gtag_UA_249290_34=1'
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'

class HackForumsSpider(scrapy.Spider):
    name = 'hackforums_spider'

    def __init__(self, output_path, avatar_path, urlsonly):
        self.base_url = "https://hackforums.net/"
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://hackforums.net/index.php'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.urlsonly = urlsonly
        self.headers = {
            'referer': 'https://hackforums.net/member.php',
            'user-agent': USER_AGENT,
            'cookie': COOKIE,
        }

    def start_requests(self):
        if self.urlsonly:
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

    def parse(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?fid=")]')
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
            '//span[contains(@id, "tid_")]'
            '/a[contains(@href, "showthread.php?tid=")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            self.output_url_file.write(thread_url)
            self.output_url_file.write('\n')

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

        next_page = response.xpath('//a[@class="pagination_next"]')
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


class HackForumsScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 16
        self.urlsonly = kwargs.get('urlsonly')
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
        process = CrawlerProcess(settings)
        process.crawl(HackForumsSpider, self.output_path, self.avatar_path, self.urlsonly)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

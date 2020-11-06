import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


USER = "hackerZone"
PASS = "CMSxHb7.-8KEA&}'"
PROXY = "socks5h://localhost:9050"
PROXY = 'http://127.0.0.1:8118'


class L33TSpider(scrapy.Spider):
    name = 'l33t_spider'

    def __init__(self, output_path, proxy):
        self.start_url = self.base_url = "http://c6dc3lkh34gyxagq.onion"
        self.proxy = proxy
        self.topic_pattern = re.compile(r'.*t=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*start=(\d+)$')
        self.output_path = output_path

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.process_login,
            meta={'proxy': self.proxy}
        )

    def process_login(self, response):
        creation_time = response.xpath(
            '//input[@name="creation_time"]/@value').extract_first()
        form_token = response.xpath(
            '//input[@name="form_token"]/@value').extract_first()
        formdata = {
            'autologin': 'on',
            'creation_time': creation_time,
            'form_token': form_token,
            'login': 'Login',
            'password': PASS,
            'redirect': './index.php?',
            'username': USER
        }
        login_url = 'http://c6dc3lkh34gyxagq.onion/ucp.php?mode=login'
        yield FormRequest(
            url=login_url,
            callback=self.parse,
            formdata=formdata,
            meta={'proxy': self.proxy}
        )

    def parse(self, response):
        forums = response.xpath(
            '//a[@class="forumtitle" or @class="subforum read"]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            yield Request(
                url=url,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
            )

        # Test for single Forum
        # url = 'http://c6dc3lkh34gyxagq.onion/viewforum.php?f=23'
        # yield Request(
        #     url=url,
        #     callback=self.parse_forum,
        #     meta={'proxy': self.proxy}
        # )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@class="topictitle"]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url.strip('.')
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                callback=self.parse_thread,
                meta={'topic_id': topic_id[0], 'proxy': self.proxy}
            )

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                meta={'proxy': self.proxy}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(int(pagination[0])/10 + 1)
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                meta={'topic_id': topic_id, 'proxy': self.proxy}
            )


class L33TScrapper():
    site_type = 'forum'

    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or PROXY
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
        process = CrawlerProcess(settings)
        process.crawl(L33TSpider, self.output_path, self.proxy)
        process.start()

if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

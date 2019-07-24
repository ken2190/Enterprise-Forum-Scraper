import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


USER = "cyrax11"
PASS = "Night#Verify098"
PROXY = 'http://127.0.0.1:8118'


class VerifiedSpider(scrapy.Spider):
    name = 'verified_spider'

    def __init__(self, output_path, proxy):
        self.start_url = self.base_url = "http://verified2ebdpvms.onion/"
        self.proxy = proxy
        self.topic_pattern = re.compile(r'.*t=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'&page=(\d+)')
        self.output_path = output_path
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Host': 'verified2ebdpvms.onion',
            'Cookie': 'IDstack=071ea59c66a0401273b0b2e31282786e9f2a93bcd013d3adc571716b1df6d629:2e78994c1804a73e6e543d8c39f635e25e798378dcea22c9c9ab1a91519c38da; bblastvisit=1562411502; bblastactivity=0; bbsessionhash=fd29e05b7c4d397d2938a3c64e88e281',
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            callback=self.parse,
            headers=self.headers,
            meta={'proxy': self.proxy}
        )

    def parse(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?f=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

        # Test for single Forum
        # url = 'http://verified2ebdpvms.onion/forumdisplay.php?f=77'
        # yield Request(
        #     url=url,
        #     callback=self.parse_forum,
        #     headers=self.headers,
        #     meta={'proxy': self.proxy}
        # )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[contains(@id, "thread_title_")]')
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
                callback=self.parse_thread,
                headers=self.headers,
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
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(pagination[0])
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
                headers=self.headers,
                meta={'topic_id': topic_id, 'proxy': self.proxy}
            )


class Verifiedv2Scrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or PROXY
        self.request_delay = 0.1
        self.no_of_threads = 16

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
        process.crawl(VerifiedSpider, self.output_path, self.proxy)
        process.start()

if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')
import sys
import os
import re
import json
import scrapy
from math import ceil
import configparser
from lxml.html import fromstring
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USER = 'BashMan'
PASS = 'LF03jCP2mfu823321'
CODE = 'superman'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) "\
             "AppleWebKit/537.36 (KHTML, like Gecko) "\
             "Chrome/75.0.3770.142 Safari/537.36"


class LCPSpider(SitemapSpider):
    name = 'lcp_spider'

    base_url = "http://84.38.187.236/"
    start_url = '{}/forums/'.format(base_url)
    topic_pattern = re.compile(r'view=.*?-(\w+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)$')
    start_url = 'http://84.38.187.236/login.php'

    use_proxy = 'On'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        action_url = response.xpath(
            '//form[@method="post"]/@action').extract_first()
        if self.base_url not in action_url:
            action_url = response.urljoin(action_url)
        code_block = response.xpath(
            '//td[input[@name="m"]]/'
            'preceding-sibling::td[1]/font/text()').extract_first()
        code_number = code_block.replace('M', '')
        code = ''
        for c in code_number:
            code += CODE[int(c) - 1]
        formdata = {
            'l': USER,
            'p': PASS,
            'm': code
        }
        yield FormRequest(
            url=action_url,
            callback=self.parse_main_page,
            formdata=formdata,
            headers=self.headers
            )

    def parse_main_page(self, response):
        forums = response.xpath(
            '//a[contains(@href, "index.php?show")]')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            "Connection": 'keep-alive',
            'Host': 'lcp.cc',
            'Referer': response.url,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': USER_AGENT
        }
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = f'{self.base_url}forum/{url}'

            yield Request(
                url=url,
                headers=headers,
                callback=self.parse_forum,
                meta={'headers': headers}
            )

    def parse_forum(self, response):
        old_pages = response.xpath(
            '//a[text()="Show Old Pages"]/@href').extract_first()
        if old_pages:
            url = f'{self.base_url}forum/{old_pages}'
            yield Request(
                url=url,
                headers=response.meta['headers'],
                callback=self.parse_forum
            )
        else:
            threads = response.xpath(
                '//a[contains(@href, "sid=")]')
            max_pages = 10
            counter = 0
            for thread in threads:
                thread_url = thread.xpath('@href').extract_first().strip('.')
                if self.base_url not in thread_url:
                    thread_url = f'{self.base_url}forum/{thread_url}'
                match = self.topic_pattern.findall(thread_url)
                if not match:
                    continue
                topic_id = str(
                    int.from_bytes(
                        match[0].encode('utf-8'), byteorder='big'
                    ) % (10 ** 7)
                )
                file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
                if os.path.exists(file_name):
                    continue
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;'
                              'q=0.9,image/webp,image/apng,*/*;'
                              'q=0.8,application/signed-exchange;v=b3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                    "Connection": 'keep-alive',
                    'Host': 'lcp.cc',
                    'Referer': response.url,
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': USER_AGENT
                }
                yield Request(
                    url=thread_url,
                    headers=headers,
                    callback=self.parse_thread,
                    meta={'topic_id': topic_id}
                )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'w') as f:
            f.write(response.text.encode('latin1', errors='ignore').decode('utf8', errors='ignore'))
            print(f'{topic_id}-{paginated_value} done..!')
            self.crawler.stats.inc_value("mainlist/detail_saved_count")

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
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


class LCPScrapper(SiteMapScrapper):
    spider_class = LCPSpider
    site_name = 'lcp.cc'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": 4,
                "AUTOTHROTTLE_MAX_DELAY": 6,
            }
        )
        return settings
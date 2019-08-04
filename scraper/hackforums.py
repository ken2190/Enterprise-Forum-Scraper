import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


def get_cookie():
    url = "https://hackforums.net/member.php?action=login"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    browser = webdriver.Chrome(
        chrome_options=options,
    )

    browser = webdriver.Chrome(chrome_options=options)
    browser.get(url)
    time.sleep(10)
    username = browser.find_element_by_xpath('//input[@name="username"]')
    username.send_keys('hackwithme123')
    time.sleep(1)
    password = browser.find_element_by_xpath('//input[@name="password"]')
    password.send_keys('LNBc:ve!h65!2i_')
    time.sleep(1)
    btn = browser.find_element_by_xpath(
        '//form[@action="member.php"]//input[@type="submit"]'
    )
    browser.execute_script("arguments[0].click();", btn)
    time.sleep(5)
    cookie = '; '.join([
        '{}={}'.format(c['name'], c['value']) for c in browser.get_cookies()
    ])
    browser.quit()
    return cookie


class HackForumsSpider(scrapy.Spider):
    name = 'hackforums_spider'

    def __init__(self, output_path):
        self.base_url = "https://hackforums.net/"
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://hackforums.net/index.php'
        self.output_path = output_path
        self.headers = {
            'referer': 'https://hackforums.net/member.php',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36',
            'cookie': get_cookie(),
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
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
            '//a[contains(@href, "showthread.php?tid=")]')
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


class HackForumsScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
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
        process.crawl(HackForumsSpider, self.output_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

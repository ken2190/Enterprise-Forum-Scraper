import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess


COOKIE = '__cfduid=d2cdf4bb92536fc8853d5c198274107fa1565064627; mybb[lastvisit]=1565064627; mybb[lastactive]=1565064680; _ga=GA1.2.94449341.1565064629; _gid=GA1.2.144744003.1565064629; cf_clearance=f2c2ff5dffd86ad21f591ec997df616d8a474539-1565064639-604800-150; loginattempts=1; mybbuser=4254128_uhB1kF2Xk6bknXbbZrkF91ogn8CmOJO2DLI0PSchUPvFuP8Xoe; myalerts=MTgwOTc2MDUwNDAzODQ%3D; mybb[gdpr]=1; sid=ce232391ea141335b5186c8d7ff1b6dd; menutabs=0; _gat_gtag_UA_249290_34=1'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:68.0) Gecko/20100101 Firefox/68.0'

COOKIE = 'cf_clearance=be9c7a1b10b4ce4ade3730170d3957a0d6e36405-1564987632-604800-250; __cfduid=d99171b5f2b30aced444e1aff6b9dd06f1564987632; mybb[lastvisit]=1564987632; mybb[lastactive]=1564987658; sid=0683abda988e5be54b8df05bb1a9e62d; menutabs=0; _ga=GA1.2.1181972070.1564987633; _gid=GA1.2.209533211.1564987633; loginattempts=1; mybbuser=3875430_Ja4F1SHgIqHiBkcBoASZMsiaJosDcE2qD696kCwz9JtQQakmCE; myalerts=MTUwMTg5NTc2ODQ5MDA%3D; mybb[gdpr]=1'
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'



def get_cookie():
    url = "https://hackforums.net/member.php?action=login"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    browser = webdriver.Firefox(options=options)
    browser.get(url)
    print('Waiting for cloudfare message to vanish')
    time.sleep(20)
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

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://hackforums.net/"
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = 'https://hackforums.net/index.php'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            'referer': 'https://hackforums.net/member.php',
            'user-agent': USER_AGENT,
            'cookie': COOKIE,
            # 'cookie': get_cookie(),
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
        process.crawl(HackForumsSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

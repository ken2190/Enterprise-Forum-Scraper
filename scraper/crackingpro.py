import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

COOKIE = 'ips4_ipsTimezone=Asia/Katmandu; ips4_hasJS=true; ips4_device_key=9fe458008094ea72f31f27709129b0a9; ips4_announcement_11=true; ips4_guestTime=1571459078; ips4_IPSSessionFront=8a322ab92e57bea0c431d1da95df791f; ips4_member_id=145208; ips4_login_key=a52cc3edb52b21e4c8430f14dccdb4bb; ips4_loggedIn=1'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
REQUEST_DELAY = 3
NO_OF_THREADS = 5


class CrackingProSpider(scrapy.Spider):
    name = 'crackingpro_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://www.crackingpro.com/"
        self.topic_pattern = re.compile(r'topic/(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*/page/(\d+)/')
        self.start_url = 'https://www.crackingpro.com/'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
            'referer': 'https://www.crackingpro.com/index.php',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'cookie': COOKIE,
            'user-agent': USER_AGENT,
        }

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse,
            dont_filter=True,
        )

    def parse(self, response):
        forums = response.xpath(
            '//div[@class="lkForumRow_main"]/h4'
            '/a[contains(@href, "/forum/")]')
        subforums = response.xpath(
            '//ul[@class="lkForumRow_subForums"]/li'
            '/a[contains(@href, "/forum/")]')
        forums.extend(subforums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if '39-exploiting-tools' not in url:
            #     continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//div[@class="ipsDataItem_main"]'
            '//span[@class="ipsType_break ipsContained"]/a')
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

        avatars = response.xpath('//li[@class="cAuthorPane_photo"]//a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if 'svg+xml' in avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
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
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class CrackingProScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
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
            'DOWNLOAD_DELAY': REQUEST_DELAY,
            'CONCURRENT_REQUESTS': NO_OF_THREADS,
            'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            'RETRY_HTTP_CODES': [403, 429, 500, 503],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

        }
        if self.proxy:
            settings.update({
                "DOWNLOADER_MIDDLEWARES": {
                    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
                    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
                    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
                },
                'ROTATING_PROXY_LIST': self.proxy,

            })
        process = CrawlerProcess(settings)
        process.crawl(CrackingProSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    kwargs = {
        'output': '/root/crackingpro'
    }
    CrackingProScrapper(kwargs).do_scrape()

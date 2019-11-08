import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

COOKIE = '__cfduid=d79daaae20279c7878c65a82f2911eca41572761787; vDDoS=0fc7da5ed7711e620eca775e5cbc3173; mybb[lastvisit]=1572761789; _ga=GA1.2.2120464920.1572761797; _gid=GA1.2.1903450472.1572761797; mybb[lastactive]=1572763315; sid=95a1baee554ebda61364268e64392734; mybb[threadread]=a%3A3%3A%7Bi%3A27677%3Bi%3A1572763245%3Bi%3A25654%3Bi%3A1572763269%3Bi%3A22749%3Bi%3A1572763315%3B%7D; mybb[forumread]=a%3A1%3A%7Bi%3A82%3Bi%3A1572763315%3B%7D; _gat_gtag_UA_121055138_2=1'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class CardingTeamSpider(scrapy.Spider):
    name = 'cardingteam_spider'

    def __init__(self, output_path, avatar_path):
        self.base_url = "https://cardingteam.cc/"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.start_url = self.base_url
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.headers = {
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
            '//strong/a[contains(@href, "Forum-")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if 'Forum-Private-Tutorials-and-Utilities' not in url:
            #     continue
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@class, "subject_") and contains(@id, "tid_")]/a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = str(
                int.from_bytes(
                    thread_url.replace('Thread-', '').encode('utf-8'), byteorder='big'
                ) % (10 ** 7)
            )
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

        next_page = response.xpath(
            '//a[@class="pagination_next"]')
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

        avatars = response.xpath(
            '//div[@class="author_avatar"]/a/img')
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

        next_page = response.xpath(
            '//div[@class="pagination"]'
            '/a[@class="pagination_next"]')
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


class CardingTeamScrapper():
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
            'RETRY_HTTP_CODES': [403, 429, 500, 503, 520],
            # 'HTTPERROR_ALLOWED_CODES': [520],
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
        process.crawl(CardingTeamSpider, self.output_path, self.avatar_path)
        process.start()


if __name__ == '__main__':
    kwargs = {
        'output': '/root/cardingteam'
    }
    CardingTeamScrapper(kwargs).do_scrape()

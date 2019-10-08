import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from scrapy.crawler import CrawlerProcess

USER = 'Exabyte'
PASS = 'Night#OG009'
REQUEST_DELAY = .6
NO_OF_THREADS = 20
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'

COOKIE = '__cfduid=d404d1323e9daf0d6901353cfd6b1939d1570002606; mybb[lastvisit]=1570002612; mybb[lastactive]=1570002626; loginattempts=1; mybbuser=158805_tFL8dFFeuwYGoojyOYMlnYwoxGZjwIKSCk7ZOJmqSuEFm1owqX; sid=caae78435600cd84809b288df5b6bf91'


class OgUsersSpider(scrapy.Spider):
    name = 'ogusers_spider'

    def __init__(self, output_path, avatar_path, useronly, firstrun):
        self.base_url = "https://ogusers.com/"
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.start_url = 'https://ogusers.com/'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.useronly = useronly
        self.firstrun = firstrun
        self.headers = {
            'referer': 'https://ogusers.com',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'cookie': COOKIE,
            'user-agent': USER_AGENT,
        }
        self.set_users_path()

    def set_users_path(self, ):
        self.user_path = os.path.join(self.output_path, 'users')
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def start_requests(self):
        if self.firstrun:
            yield Request(
                url=self.start_url,
                headers=self.headers,
                callback=self.parse
            )
        else:
            input_file = self.output_path + '/urls.txt'
            if os.path.exists(input_file):
                for thread_url in open(input_file, 'r'):
                    thread_url = thread_url.strip()
                    topic_id = str(
                        int.from_bytes(
                            thread_url.encode('utf-8'), byteorder='big'
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
            else:
                yield Request(
                    url=self.start_url,
                    headers=self.headers,
                    callback=self.parse
                )

    def proceed_for_login(self, response):
        my_post_key = response.xpath(
            '//input[@name="my_post_key"]/@value').extract_first()
        formdata = {
            'action': 'do_login',
            'url': 'https://ogusers.com/',
            'my_post_key': my_post_key,
            'quick_login': '1',
            'username': USER,
            'password': PASS,
            '2facode': '',
            "remember": 'yes',
            'submit': 'Login'
        }
        login_url = 'https://ogusers.com/member.php'
        yield FormRequest(
            url=login_url,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse,
            dont_filter=True,
        )

    def parse(self, response):
        forum_urls = list()
        forums = response.xpath(
            '//td[@class="col_row"]/a[contains(@href, "Forum-")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            forum_urls.append(url)
            sub_forums = forum.xpath(
                'following-sibling::div[1][@class="smalltext"]'
                '/div/a[contains(@href, "Forum-")]')
            for sub_forum in sub_forums:
                url = sub_forum.xpath('@href').extract_first()
                if self.base_url not in url:
                    url = self.base_url + url
                forum_urls.append(url)
        for url in forum_urls:
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'forum_name': url.rsplit('/', 1)[-1]}
            )

    def parse_forum(self, response):
        forum_name = response.meta['forum_name']
        output_url_file = None
        if self.firstrun:
            output_url_file = open(
                self.output_path + f'/{forum_name}.txt', 'a')
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@id, "tid_")]/a[contains(@href, "Thread-")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            if output_url_file:
                output_url_file.write(thread_url)
                output_url_file.write('\n')
            else:
                topic_id = str(
                    int.from_bytes(
                        thread_url.encode('utf-8'), byteorder='big'
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

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta={'forum_name': forum_name}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        if not self.useronly:
            pagination = self.pagination_pattern.findall(response.url)
            paginated_value = pagination[0] if pagination else 1
            file_name = '{}/{}-{}.html'.format(
                self.output_path, topic_id, paginated_value)
            with open(file_name, 'wb') as f:
                f.write(response.text.encode('utf-8'))
                print(f'{topic_id}-{paginated_value} done..!')

        users = response.xpath('//div[@class="postbitdetail"]/span/a')
        for user in users:
            user_url = user.xpath('@href').extract_first()
            if self.base_url not in user_url:
                user_url = self.base_url + user_url
            user_name = user.xpath('span/text()').extract_first()
            if not user_name:
                user_name = user.xpath('text()').extract_first()
            if not user_name:
                user_name = user.xpath('font/text()').extract_first()
            file_name = '{}/{}.html'.format(self.user_path, user_name)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=user_url,
                headers=self.headers,
                callback=self.parse_user,
                meta={
                    'file_name': file_name,
                    'user_name': user_name
                }
            )

        avatars = response.xpath('//div[@class="postbit-avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if 'image/svg' in avatar_url:
                continue
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
            '//div[@class="pagination"]//a[@class="pagination_next"]')
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

    def parse_user(self, response):
        file_name = response.meta['file_name']
        user_name = response.meta['user_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"User {user_name} done..!")
        user_history = response.xpath(
            '//div[@class="usernamehistory"]/a')
        if user_history:
            history_url = user_history.xpath('@href').extract_first()
            if self.base_url not in history_url:
                history_url = self.base_url + history_url
            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta={'user_name': user_name}
            )

    def parse_user_history(self, response):
        user_name = response.meta['user_name']
        file_name = '{}/{}-history.html'.format(self.user_path, user_name)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"History for user {user_name} done..!")

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class OgUsersScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.useronly = kwargs.get('useronly')
        self.proxy = kwargs.get('proxy') or None
        self.firstrun = kwargs.get('firstrun')
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
                    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
                    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
                },
                'ROTATING_PROXY_LIST': self.proxy,

            })
        process = CrawlerProcess(settings)
        process.crawl(OgUsersSpider, self.output_path,
                      self.avatar_path, self.useronly, self.firstrun)
        process.start()

import os
import re
import datetime
import sqlite3
import dateutil.parser as dparser
from scrapy.http import Request
from scrapy.crawler import CrawlerProcess
from scraper.base_scrapper import BypassCloudfareSpider


REQUEST_DELAY = 0.3
NO_OF_THREADS = 10


class RaidForumsSpider(BypassCloudfareSpider):

    name = 'raidforums_spider'

    def __init__(self, output_path, useronly, update, db_path, avatar_path):
        self.base_url = "https://raidforums.com/"
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.username_pattern = re.compile(r'User-(.*)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.start_url = 'https://raidforums.com/'
        self.output_path = output_path
        self.useronly = useronly
        self.update = update
        self.db_path = db_path
        self.avatar_path = avatar_path
        self.headers = {
            "user-agent": self.custom_settings.get("DEFAULT_REQUEST_HEADERS")
        }
        self.set_users_path()

    def set_users_path(self, ):
        self.user_path = os.path.join(self.output_path, 'users')
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def start_requests(self):
        yield Request(
            url=self.start_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response):
        if self.update:
            if not self.update_required():
                return
            update_url = 'https://raidforums.com/search.php?action=getdaily'
            self.headers = {
                'referer': 'https://raidforums.com/',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'user-agent': self.custom_settings.get("DEFAULT_REQUEST_HEADERS")
            }
            yield Request(
                url=update_url,
                headers=self.headers,
                callback=self.parse_new_posts
            )
        else:
            forums = response.xpath(
                '//a[contains(@href, "Forum-")]')
            for forum in forums:
                url = forum.xpath('@href').extract_first()
                if self.base_url not in url:
                    url = self.base_url + url
                yield Request(
                    url=url,
                    callback=self.parse_forum
                )

    def update_required(self, ):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        check_query = "SELECT last_scraped from forum_info WHERE name='raidforums'"
        result = self.cursor.execute(check_query)
        scraped_date = dparser.parse(result.fetchone()[0]).date()
        self.conn.close()
        if datetime.datetime.now().date() <= scraped_date:
            print('INFO: last_scraped date in db is same as today\'s date')
            return False
        return True

    def parse_new_posts(self, response):
        threads = response.xpath(
            '//a[text()="New"]')

        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = str(
                int.from_bytes(
                    thread_url.encode('utf-8'), byteorder='big'
                ) % (10 ** 7)
            )
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
                callback=self.parse_new_posts
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@class="forum-display__thread-name"]')
        if not self.useronly:
            for thread in threads:
                thread_url = thread.xpath('@href').extract_first()
                if self.base_url not in thread_url:
                    thread_url = self.base_url + thread_url
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

        users = response.xpath('//span[@class="author smalltext"]/a')
        for user in users:
            user_url = user.xpath('@href').extract_first()
            if self.base_url not in user_url:
                user_url = self.base_url + user_url
            user_id = self.username_pattern.findall(user_url)
            if not user_id:
                continue
            file_name = '{}/{}.html'.format(self.user_path, user_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=user_url,
                headers=self.headers,
                callback=self.parse_user,
                meta={
                    'file_name': file_name,
                    'user_id': user_id[0]
                }
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                # headers=self.headers,
                callback=self.parse_forum
            )

    def parse_user(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"User {response.meta['user_id']} done..!")
        user_history = response.xpath(
            '//span[text()="Username Changes:"]'
            '/following-sibling::a[1]'
        )
        if user_history:
            history_url = user_history.xpath('@href').extract_first()
            if self.base_url not in history_url:
                history_url = self.base_url + history_url
            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta={'user_id': response.meta['user_id']}
            )

    def parse_user_history(self, response):
        user_id = response.meta['user_id']
        file_name = '{}/{}-history.html'.format(self.user_path, user_id)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f"History for user {user_id} done..!")

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        if self.update:
            pagination = response.xpath(
                '//span[@class="pagination_current"]/text()').extract_first()
            paginated_value = pagination if pagination else 1
        else:
            pagination = self.pagination_pattern.findall(response.url)
            paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath('//a[@class="post__user-avatar"]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
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
            '//section[@id="thread-navigation"]//a[@class="pagination_next"]')
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


class RaidForumsScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.useronly = kwargs.get('useronly')
        self.update = kwargs.get('update')
        self.db_path = kwargs.get('db_path')
        self.proxy = kwargs.get('proxy') or None
        self.ensure_avatar_path()

    def ensure_avatar_path(self, ):
        self.avatar_path = f'{self.output_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def do_scrape(self):
        settings = {
            "DOWNLOADER_MIDDLEWARES": {
                'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            },
            'DOWNLOAD_DELAY': REQUEST_DELAY,
            'CONCURRENT_REQUESTS': NO_OF_THREADS,
            'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            'RETRY_HTTP_CODES': [403, 406, 429, 500, 503],
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
        process.crawl(
            RaidForumsSpider,
            self.output_path,
            self.useronly,
            self.update,
            self.db_path,
            self.avatar_path
        )
        process.start()
        if self.update:
            self.update_db()

    def update_db(self, ):
        print('.....FINISHED.....UDPATING DB')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        today = datetime.datetime.now().date()
        update_query = "UPDATE forum_info SET last_scraped='{}' WHERE name='raidforums'".format(today)
        result = self.cursor.execute(update_query)
        print(result.fetchone())
        self.conn.commit()
        self.conn.close()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

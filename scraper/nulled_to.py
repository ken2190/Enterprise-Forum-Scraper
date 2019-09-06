import time
import requests
import os
import json
import re
import scrapy
from math import ceil
from copy import deepcopy
from urllib.parse import urlencode
import configparser
from scrapy.http import Request, FormRequest
from lxml.html import fromstring
from scrapy.crawler import CrawlerProcess


COOKIE = '__cfduid=dc9024d1e263a42aca3be0ec879e14ee81567498330; _ga=GA1.2.882200545.1567498338; nulledmember_id=2864575; nulledpass_hash=0ce8307c5a89f209dcd1635c03ec70e8; ipsconnect_4ac7fd4073b08692edf97bb68b9b88dd=1; nulledmember_id=2864575; nulledpass_hash=0ce8307c5a89f209dcd1635c03ec70e8; cf_clearance=ebe5d0e66db59c0d8daa3972642a36c4136703d4-1567793880-86400-150; PHPSESSID=31sss46apedkmhm8rqqrcplsd2; nulledsession_id=1bec061af690b59d0bc22209e316a348; _gid=GA1.2.414405257.1567793883; _gat=1'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'

FORUMS = [
    'https://www.nulled.to/forum/2-announcements/',
    'https://www.nulled.to/forum/209-releases/',
    'https://www.nulled.to/forum/110-feedback-and-suggestions/',
    'https://www.nulled.to/forum/32-support/',
    'https://www.nulled.to/forum/125-archive/',
    'https://www.nulled.to/forum/3-the-lounge/',
    'https://www.nulled.to/forum/114-crypto-currencies/',
    'https://www.nulled.to/forum/93-entertainment/',
    'https://www.nulled.to/forum/204-personal-life/',
    'https://www.nulled.to/forum/115-achievements-bragging/',
    'https://www.nulled.to/forum/62-gaming/',
    'https://www.nulled.to/forum/35-graphics/',
    'https://www.nulled.to/forum/7-cracked-programs/',
    'https://www.nulled.to/forum/43-accounts/',
    'https://www.nulled.to/forum/184-dumps-databases/',
    'https://www.nulled.to/forum/24-source-codes-scripts/',
    'https://www.nulled.to/forum/9-e-books-guides-and-tutorials/',
    'https://www.nulled.to/forum/15-other-leaks/',
    'https://www.nulled.to/forum/117-requests/',
    'https://www.nulled.to/forum/41-vip-general-chat/',
    'https://www.nulled.to/forum/42-vip-leaks/',
    'https://www.nulled.to/forum/44-vip-dumps/',
    'https://www.nulled.to/forum/90-cracking-tools/',
    'https://www.nulled.to/forum/98-cracking-tutorials-information/',
    'https://www.nulled.to/forum/91-cracking-support/',
    'https://www.nulled.to/forum/73-configs/',
    'https://www.nulled.to/forum/74-combolists/',
    'https://www.nulled.to/forum/49-proxies/',
    'https://www.nulled.to/forum/57-beginner-hacking/',
    'https://www.nulled.to/forum/99-advanced-hacking/',
    'https://www.nulled.to/forum/58-hacking-tutorials/',
    'https://www.nulled.to/forum/70-monetizing-techniques/',
    'https://www.nulled.to/forum/69-social-engineering/',
    'https://www.nulled.to/forum/201-e-whoring/',
    'https://www.nulled.to/forum/122-amazon/',
    'https://www.nulled.to/forum/51-visual-basic-and-net-framework/',
    'https://www.nulled.to/forum/52-cc-obj-c-programming/',
    'https://www.nulled.to/forum/55-assembly-language-and-programming/',
    'https://www.nulled.to/forum/53-java-language-jvm-and-the-jre/',
    'https://www.nulled.to/forum/54-phphtmlcsssql-development/',
    'https://www.nulled.to/forum/100-lua/',
    'https://www.nulled.to/forum/135-coding-and-programming/',
    'https://www.nulled.to/forum/157-marketplace-lobby/',
    'https://www.nulled.to/forum/60-premium-sellers/',
    'https://www.nulled.to/forum/46-secondary-sellers/',
    'https://www.nulled.to/forum/47-buyers/',
    'https://www.nulled.to/forum/61-trading-station/',
    'https://www.nulled.to/forum/195-service-requests/',
    'https://www.nulled.to/forum/171-archive/',
    'https://www.nulled.to/forum/11-general-chat/',
    'https://www.nulled.to/forum/12-reverse-engineering-guides-and-tips/',
    'https://www.nulled.to/forum/14-tools/',
    'https://www.nulled.to/forum/192-motm/',
    'https://www.nulled.to/forum/33-answered/',
    'https://www.nulled.to/forum/178-account-recovery/',
    'https://www.nulled.to/forum/132-ban-appeals/',
    'https://www.nulled.to/forum/134-hq-lounge/',
    'https://www.nulled.to/forum/5-introductions/',
    'https://www.nulled.to/forum/186-news-and-politics/',
    'https://www.nulled.to/forum/94-music/',
    'https://www.nulled.to/forum/95-movies-series/',
    'https://www.nulled.to/forum/97-leaks/',
    'https://www.nulled.to/forum/66-league-of-legends/',
    'https://www.nulled.to/forum/208-fortnite/',
    'https://www.nulled.to/forum/64-fps/',
    'https://www.nulled.to/forum/63-mmo/',
    'https://www.nulled.to/forum/101-other-games/',
    'https://www.nulled.to/forum/126-graphic-resources/',
    'https://www.nulled.to/forum/36-paid-graphic-work/',
    'https://www.nulled.to/forum/18-mmo-bots/',
    'https://www.nulled.to/forum/19-moba-bots/',
    'https://www.nulled.to/forum/149-youtube-twitter-and-fb-bots/',
    'https://www.nulled.to/forum/20-malicious-software/',
    'https://www.nulled.to/forum/21-miscellaneous/',
    'https://www.nulled.to/forum/30-exploits/',
    'https://www.nulled.to/forum/25-ccobj-c/',
    'https://www.nulled.to/forum/27-net-framework/',
    'https://www.nulled.to/forum/29-php-css-jvscript/',
    'https://www.nulled.to/forum/198-combos/',
    'https://www.nulled.to/forum/199-accounts/',
    'https://www.nulled.to/forum/210-openbullet/',
    'https://www.nulled.to/forum/211-sentry-mba/',
    'https://www.nulled.to/forum/212-blackbullet/',
    'https://www.nulled.to/forum/213-storm/',
    'https://www.nulled.to/forum/214-snipr/',
    'https://www.nulled.to/forum/188-dorks/',
    'https://www.nulled.to/forum/59-website-and-forum-hacking/',
    'https://www.nulled.to/forum/145-resources/',
    'https://www.nulled.to/forum/146-discussion/',
    'https://www.nulled.to/forum/147-help/',
    'https://www.nulled.to/forum/148-tutorials/',
    'https://www.nulled.to/forum/137-c/',
    'https://www.nulled.to/forum/136-net-leaks-downloads/',
    'https://www.nulled.to/forum/139-cc-leaks-downloads/',
    'https://www.nulled.to/forum/141-java-leaks-downloads/',
    'https://www.nulled.to/forum/140-php-leaks-downloads/',
    'https://www.nulled.to/forum/142-other-leaks/',
    'https://www.nulled.to/forum/159-scam-reports/',
    'https://www.nulled.to/forum/129-products/',
    'https://www.nulled.to/forum/128-accounts/',
    'https://www.nulled.to/forum/127-services/',
    'https://www.nulled.to/forum/160-e-books-monetizing-guides/',
    'https://www.nulled.to/forum/161-combos-configs/',
    'https://www.nulled.to/forum/177-accounts/',
    'https://www.nulled.to/forum/163-products/',
    'https://www.nulled.to/forum/164-services/',
    'https://www.nulled.to/forum/191-graphics-marketplace/',
    'https://www.nulled.to/forum/165-currency-exchange/',
    'https://www.nulled.to/forum/196-partnership-hiring/',
    'https://www.nulled.to/forum/197-favors-rewards/',
]


class NulledSpider(scrapy.Spider):
    name = 'nulled_spider'

    def __init__(self, output_path, avatar_path=None, urlsonly=None):
        self.base_url = "https://www.nulled.to"
        self.topic_pattern = re.compile(r'topic/(\d+)')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page-(\d+)')
        self.start_url = 'https://www.nulled.to'
        self.output_path = output_path
        self.avatar_path = avatar_path
        self.urlsonly = urlsonly
        self.headers = {
            'user-agent': USER_AGENT,
            'cookie': COOKIE,
            'referer': 'https://www.nulled.to/',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1'
        }

    def start_requests(self):
        # Proceed for banlist
        if not self.avatar_path:
            ban_url = 'https://www.nulled.to/ban-list.php'
            yield Request(
                url=ban_url,
                headers=self.headers,
                callback=self.parse_ban_list,
                meta={'pagination': 1}
            )
        elif self.urlsonly:
            for forum_url in FORUMS:
                identifier = re.findall(r'forum/(.*)/', forum_url)[0]
                file_name = f'{self.output_path}/{identifier}.txt'
                if not os.path.exists(file_name):
                    self.output_url_file = open(file_name, 'w')
                    yield Request(
                        url=forum_url,
                        headers=self.headers,
                        callback=self.parse_forum
                    )
                    break
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

    def parse_ban_list(self, response):
        pagination = response.meta['pagination']
        file_name = '{}/page-{}.html'.format(
            self.output_path, pagination)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'page-{pagination} done..!')
        last_page = response.xpath('//li[@class="last"]/a')
        if last_page and pagination == 1:
            last_page_index = last_page.xpath('@href').re(r'st=(\d+)')
            for st in range(50, int(last_page_index[0]) + 50, 50):
                url = f'https://www.nulled.to/ban-list.php?&st={st}'
                pagination += 1
                yield Request(
                    url=url,
                    headers=self.headers,
                    callback=self.parse_ban_list,
                    meta={'pagination': pagination}
                )

    def parse_forum_names(self, response):
        forums = response.xpath(
            '//h4[@class="forum_name"]/strong/a')
        sub_forums = response.xpath(
            '//li/i[@class="fa fa-folder"]'
            '/following-sibling::a[1]')
        forums.extend(sub_forums)
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            print(url)

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@itemprop="url" and contains(@id, "tid-link-")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            self.output_url_file.write(thread_url)
            self.output_url_file.write('\n')

        next_page = response.xpath('//li[@class="next"]/a')
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
            '//li[@class="avatar"]/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            match = self.avatar_name_pattern.findall(avatar_url)
            if not match:
                continue
            file_name = '{}/{}'.format(self.avatar_path, match[0])
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

        next_page = response.xpath('//li[@class="next"]/a')
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


class NulledToScrapper():
    def __init__(self, kwargs):
        self.output_path = kwargs.get('output')
        self.proxy = kwargs.get('proxy') or None
        self.request_delay = 0.1
        self.no_of_threads = 16
        self.urlsonly = kwargs.get('urlsonly')
        self.banlist_path = None
        self.avatar_path = None
        if kwargs.get('banlist'):
            self.ensure_ban_path()
        else:
            self.ensure_avatar_path()

    def ensure_ban_path(self, ):
        self.banlist_path = f'{self.output_path}/banlist'
        if not os.path.exists(self.banlist_path):
            os.makedirs(self.banlist_path)

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
            'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            'RETRY_TIMES': 10,
            'LOG_ENABLED': True,

        }
        process = CrawlerProcess(settings)
        if self.banlist_path:
            process.crawl(
                NulledSpider, self.banlist_path,
            )
        else:
            process.crawl(
                NulledSpider, self.output_path,
                self.avatar_path, self.urlsonly
            )
        process.start()


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

import os
import re
import time
import scrapy

from glob import glob
from requests import Session
from lxml.html import fromstring
from requests.exceptions import ConnectionError
from scrapy.crawler import CrawlerProcess
from copy import deepcopy
from datetime import datetime

from scrapy import (
    Request,
    Selector
)


###############################################################################
# Base Scraper
###############################################################################


class BaseScrapper:

    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))\
            if kwargs.get('topic_start') else None
        self.topic_end_count = int(kwargs.get('topic_end')) + 1\
            if kwargs.get('topic_end') else None
        self.output_path = kwargs.get('output')
        self.wait_time = int(kwargs.get('wait_time'))\
            if kwargs.get('wait_time') else 1
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'
        }
        self.session = Session()
        if kwargs.get('proxy'):
            self.session.proxies = {
                'http': kwargs.get('proxy'),
                'https': kwargs.get('proxy'),
            }
        self.avatar_name_pattern = None
        self.cloudfare_error = None
        self.retry = False
        self.ensure_avatar_path()
        if kwargs.get('daily'):
            self.ensure_daily_output_path()

    def ensure_daily_output_path(self,):
        folder_name = datetime.now().date().isoformat()
        self.output_path = f'{self.output_path}/{folder_name}'
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def ensure_avatar_path(self, ):
        self.avatar_path = f'{self.output_path}/avatars'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def get_broken_file_topics(self,):
        broken_topics = []
        file_pattern = re.compile(r'.*/(\d+)-?1?\.html')
        for _file in glob(self.output_path+'/*'):
            topic_match = file_pattern.findall(_file)
            if topic_match and os.path.getsize(_file) < 4*1024:
                broken_topics.append(topic_match[0])
        return broken_topics

    def get_page_content(
        self,
        url,
        ignore_xpath=None,
        continue_xpath=None,
        topic=None
    ):
        try:
            response = self.session.get(url, headers=self.headers)
            content = response.content
            html_response = self.get_html_response(content)
            if ignore_xpath and html_response.xpath(ignore_xpath) and topic:
                error_file = f'{self.output_path}/{topic}.txt'
                with open(error_file, 'wb') as f:
                    return
            if continue_xpath and html_response.xpath(continue_xpath):
                return self.get_page_content(
                    url, ignore_xpath, continue_xpath)
            if self.cloudfare_error and html_response.xpath(
               self.cloudfare_error):
                if self.cloudfare_count < 5:
                    self.cloudfare_count += 1
                    time.sleep(60)
                    return self.get_page_content(
                        url, ignore_xpath, continue_xpath)
                else:
                    return
            return content
        except ConnectionError:
            if not self.retry:
                self.retry = True
                return self.get_page_content(
                    url, ignore_xpath, continue_xpath)

            return
        except:
            # traceback.print_exc()
            return

    def process_user_profile(
        self,
        uid,
        url,
    ):
        self.retry = False
        output_file = f'{self.output_path}/UID-{uid}.html'
        if os.path.exists(output_file):
            return
        time.sleep(self.wait_time)
        content = self.get_page_content(url)
        if not content:
            return
        with open(output_file, 'wb') as f:
            f.write(content)
        print(f'UID-{uid} done..!')
        return

    def process_first_page(
        self,
        topic,
        ignore_xpath=None,
        continue_xpath=None
    ):
        self.cloudfare_count = 0
        self.retry = False
        initial_file = f'{self.output_path}/{topic}-1.html'
        if os.path.exists(initial_file):
            return
        error_file = f'{self.output_path}/{topic}.txt'
        if os.path.exists(error_file):
            return
        time.sleep(self.wait_time)
        url = self.topic_url.format(topic)
        content = self.get_page_content(
            url,
            ignore_xpath,
            continue_xpath,
            topic
        )
        if not content:
            print(f'No data for url: {url}')
            return

        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
        html_response = self.get_html_response(content)
        return html_response

    def process_pagination(self, response):
        while True:
            paginated_content = self.write_paginated_data(response)
            if not paginated_content:
                return
            response = self.get_html_response(paginated_content)
            avatar_info = self.get_avatar_info(response)
            for name, url in avatar_info.items():
                self.save_avatar(name, url)

    def save_avatar(self, name, url):
        self.retry = False
        avatar_file = f'{self.avatar_path}/{name}'
        if os.path.exists(avatar_file):
            return
        time.sleep(self.wait_time)
        content = self.get_page_content(url)
        if not content:
            return
        with open(avatar_file, 'wb') as f:
            f.write(content)


class BaseTorScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.proxy = kwargs.get("proxy")
        if self.proxy is None:
            raise ValueError(
                "Tor scraper require tor proxy parameter. -x or --proxy"
            )


class SiteMapScrapper:

    settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
        },
        "RETRY_HTTP_CODES": [403, 406, 429, 500, 503],
        "RETRY_TIMES": 5,
        "LOG_ENABLED": True,
        "LOG_STDOUT": True
    }

    time_format = "%Y-%m-%d"

    spider_class = None

    def __init__(self, kwargs):
        self.output_path = kwargs.get("output")
        self.useronly = kwargs.get("useronly")
        self.start_date = kwargs.get("start_date")
        self.ensure_avatar_path(kwargs.get("template"))

        if self.start_date:
            try:
                self.start_date = datetime.strptime(
                    self.start_date,
                    self.time_format
                )
            except Exception as err:
                raise ValueError(
                    "Wrong date format. Correct format is: %s. Detail: %s" % (
                        self.time_format,
                        err
                    )
                )

    def load_settings(self):
        return deepcopy(self.settings)

    def load_spider_kwargs(self):
        return {
            "output_path": getattr(self, "output_path", None),
            "useronly": getattr(self, "useronly", None),
            "avatar_path": getattr(self, "avatar_path", None),
            "start_date": getattr(self, "start_date", None)
        }

    def ensure_avatar_path(self, template):
        self.avatar_path = f'../avatars/{template}'
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def do_scrape(self):
        process = CrawlerProcess(
            self.load_settings()
        )
        process.crawl(
            self.spider_class,
            **self.load_spider_kwargs()
        )
        process.start()


class FromDateScrapper(BaseScrapper, SiteMapScrapper):

    from_date_spider_class = None
    time_format = "%Y-%m-%d"

    def __init__(self, kwargs):
        super().__init__(kwargs)
        self.start_date = kwargs.get("start_date")
        if self.start_date:
            self.start_date = datetime.strptime(
                self.start_date,
                self.time_format
            )

    def do_scrape_from_date(self):
        process = CrawlerProcess(
            self.load_settings()
        )
        process.crawl(
            self.from_date_spider_class,
            **self.load_spider_kwargs()
        )
        process.start()



###############################################################################
# Base Spider
###############################################################################


class BypassCloudfareSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "middlewares.middlewares.LuminatyProxyMiddleware": 100,
            "middlewares.middlewares.BypassCloudfareMiddleware": 200
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
        }
    }


class BypassCloudfareNoProxySpider(scrapy.Spider):

    download_delay = 0.3
    download_thread = 10

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "middlewares.middlewares.BypassCloudfareMiddleware": 200
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
        },
        'DOWNLOAD_DELAY': download_delay,
        'CONCURRENT_REQUESTS': download_thread,
        'CONCURRENT_REQUESTS_PER_DOMAIN': download_thread
    }


class SitemapSpider(BypassCloudfareSpider):

    # Url stuffs
    base_url = None
    sitemap_url = None

    # Format stuff
    sitemap_datetime_format = "%Y-%m-%dT%H:%MZ"

    # Xpath stuffs
    forum_xpath = None
    thread_xpath = None
    thread_url_xpath = None
    thread_date_xpath = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_path = kwargs.get("output_path")
        self.useronly = kwargs.get("useronly")
        self.avatar_path = kwargs.get("avatar_path")
        self.start_date = kwargs.get("start_date")
        self.cookies = kwargs.get("cookies")
        self.headers = {
            "user-agent": self.custom_settings.get("DEFAULT_REQUEST_HEADERS")
        }

        if self.cookies:
            self.cookies = self.load_cookies(self.cookies)

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date,
            self.sitemap_datetime_format
        )

    def parse_thread_url(self, thread_url):
        return thread_url

    def load_cookies(self, cookies_string):
        cookies_elements = [
            element.strip().split("=") for element in cookies_string.split(";")
        ]
        cookies = {
            element[0]: "=".join(element[1:]) for element in cookies_elements
        }
        return cookies

    def start_requests(self):
        if self.start_date:
            yield scrapy.Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers
            )

    def parse_sitemap(self, response):

        # Load selector
        selector = Selector(text=response.text)

        # Load forum
        all_forum = selector.xpath(self.forum_xpath).extract()

        for forum in all_forum:
            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_sitemap_forum
            )

    def parse_sitemap_forum(self, response):

        # Load selector
        selector = Selector(text=response.text)

        # Load thread
        all_threads = selector.xpath(self.thread_xpath).extract()

        for thread in all_threads:
            yield from self.parse_sitemap_thread(thread)

    def parse_sitemap_thread(self, thread):

        # Load selector
        selector = Selector(text=thread)

        # Load thread url and update
        thread_url = self.parse_thread_url(
            selector.xpath(self.thread_url_xpath).extract_first()
        )
        thread_date = self.parse_thread_date(
            selector.xpath(self.thread_date_xpath).extract_first()
        )

        if self.start_date > thread_date:
            self.logger.info(
                "Thread %s ignored because last update in the past. Detail: %s" % (
                    thread_url,
                    thread_date
                )
            )
            return

        topic_id = self.get_topic_id(thread_url)
        if not topic_id:
            return

        # Load request arguments
        request_arguments = {
            "url": thread_url,
            "headers": self.headers,
            "callback": self.parse_thread,
            "meta": {
                "topic_id": topic_id
            }
        }
        if self.cookies:
            request_arguments["cookies"] = self.cookies

        yield Request(**request_arguments)

    def get_topic_id(self, url=None):
        topic_id = str(
            int.from_bytes(
                url.encode('utf-8'),
                byteorder='big'
            ) % (10 ** 7)
        )
        return topic_id

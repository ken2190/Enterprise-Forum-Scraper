import os
import re
import time
import scrapy
import uuid

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
        "RETRY_HTTP_CODES": [406, 429, 500],
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
        self.set_users_path()

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
            "start_date": getattr(self, "start_date", None),
            "user_path": getattr(self, "user_path", None)
        }

    def set_users_path(self):
        self.user_path = os.path.join(
            self.output_path,
            'users'
        )
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

    def ensure_avatar_path(self, template):
        if getattr(self, 'site_name', None):
            self.avatar_path = f'../avatars/{self.site_name}'
        else:
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

    use_proxy = True
    download_delay = 0.3
    download_thread = 10
    default_useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) " \
                        "Gecko/20100101 Firefox/71.0"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        if (crawler.settings.frozen):
            crawler.settings.frozen = False

            # Default settings
            crawler.settings.set(
                "DEFAULT_REQUEST_HEADERS",
                {
                    "User-Agent": cls.default_useragent
                }
            )

            # Proxy settings
            if cls.use_proxy:
                crawler.settings.set(
                    "DOWNLOADER_MIDDLEWARES",
                    {
                        "middlewares.middlewares.LuminatyProxyMiddleware": 100,
                        "middlewares.middlewares.BypassCloudfareMiddleware": 200
                    },
                )
            else:
                crawler.settings.set(
                    "DOWNLOADER_MIDDLEWARES",
                    {
                        "middlewares.middlewares.BypassCloudfareMiddleware": 200
                    },
                )
                crawler.settings.set(
                    "DOWNLOAD_DELAY",
                    cls.download_delay
                )
                crawler.settings.set(
                    "CONCURRENT_REQUESTS",
                    cls.download_thread
                )
                crawler.settings.set(
                    "CONCURRENT_REQUESTS_PER_DOMAIN",
                    cls.download_thread
                )

            # Free settings
            crawler.settings.freeze()

        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider


class SitemapSpider(BypassCloudfareSpider):

    # Url stuffs
    base_url = None
    sitemap_url = None

    # Payload stuffs
    post_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Format stuff
    sitemap_datetime_format = "%Y-%m-%dT%H:%MZ"  # Date time format of majority of sitemap lastmod/thread last update time #
    post_datetime_format = "%m-%d-%Y"  # Date time format of majority of post update time #

    # Xpath stuffs

    # Forum xpath #
    forum_sitemap_xpath = None  # Xpath of forum url in the forum sitemap #
    forum_xpath = None  # Xpath of forum url in the main entry forum #
    pagination_xpath = None  # Xpath of next button in forum detail #

    # Thread xpath #
    thread_sitemap_xpath = None  # Xpath of the whole block of thread in thread sitemap #
    thread_url_xpath = None  # Xpath of thread url in thread sitemap #
    thread_lastmod_xpath = None  # Xpath of thread lastmod in thread sitemap #

    thread_xpath = None
    thread_first_page_xpath = None  # Xpath of thread url in forum detail #
    thread_last_page_xpath = None  # Xpath of thread url last page in forum detail (if exist) #
    thread_date_xpath = None  # Xpath of thread last post update time in forum detail #
    thread_page_xpath = None  # Xpath of current page button in thread detail #
    thread_pagination_xpath = None  # Xpath of previous button in thread pagination #

    # Post xpath #
    post_date_xpath = None  # Xpath of post update time in thread detail #

    # Avatar xpath #
    avatar_xpath = None  # Xpath to define location of avatar url #

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Init stuffs
        self.output_path = kwargs.get("output_path")
        self.useronly = kwargs.get("useronly")
        self.avatar_path = kwargs.get("avatar_path")
        self.user_path = kwargs.get("user_path")
        self.start_date = kwargs.get("start_date")

        # Handle headers
        self.headers = {
            "User-Agent": self.default_useragent
        }
        self.post_headers.update(self.headers)

        # Handle cookies
        self.cookies = kwargs.get("cookies")
        if self.cookies:
            self.cookies = self.load_cookies(self.cookies)

        # Handle code file
        self.backup_code_file = os.path.join(
            os.getcwd(),
            "code/%s" % self.name
        )
        if not os.path.exists(self.backup_code_file):
            self.backup_code_file = None
            self.backup_codes = []
        else:
            with open(
                file=self.backup_code_file,
                mode="r",
                encoding="utf-8"
            ) as file:
                self.backup_codes = [
                    code.strip() for code in file.read().split("\n")
                ]

    def write_backup_codes(self):
        with open(
            file=self.backup_code_file,
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(
                "\n".join(self.backup_codes)
            )

    def synchronize_headers(self, response):
        self.headers.update(
            {
                "User-Agent": response.request.headers.get("User-Agent")
            }
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)

        return meta

    def extract_thread_stats(self, thread):
        """
        :param thread: str => thread html contain url and last mod
        :return: thread url: str, thread lastmod: datetime
        """
        # Load selector
        selector = Selector(text=thread)

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = selector.xpath(
                self.thread_first_page_xpath
            ).extract_first()

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = selector.xpath(
                self.thread_last_page_xpath
            ).extract_first()

        thread_lastmod = selector.xpath(
            self.thread_date_xpath
        ).extract_first()

        # Process stats
        try:
            thread_url = (self.parse_thread_url(thread_last_page_url)
                          or self.parse_thread_url(thread_first_page_url))
        except Exception as err:
            thread_url = None

        try:
            thread_lastmod = self.parse_thread_date(thread_lastmod)
        except Exception as err:
            thread_lastmod = None

        return thread_url, thread_lastmod

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        return datetime.strptime(
            thread_date.strip(),
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip(),
            self.post_datetime_format
        )

    def parse_thread_url(self, thread_url):
        """
        :param thread_url: str => thread url as string
        :return: str => thread url as string
        """
        if thread_url:
            return thread_url.strip()
        else:
            return

    def get_topic_id(self, url=None):
        """
        :param url: str => thread url
        :return: str => extracted topic id from thread url
        """
        if getattr(self, "topic_pattern", None):
            try:
                return self.topic_pattern.findall(url)[0]
            except Exception as err:
                return

        topic_id = str(
            int.from_bytes(
                url.encode('utf-8'),
                byteorder='big'
            ) % (10 ** 7)
        )

        return topic_id

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        if getattr(self, "avatar_name_pattern", None):
            try:
                return os.path.join(
                    self.avatar_path,
                    self.avatar_name_pattern.findall(url)[0]
                )
            except Exception as err:
                return

        return
    
    def get_existing_file_date(self, topic_id):

        # Load first page file name
        file_name = os.path.join(
            self.output_path,
            "%s-1.html" % topic_id
        )

        # If file name exist then return
        if not os.path.exists(file_name):
            return

        # Else return time stamp
        created_ts = os.stat(file_name).st_ctime
        return datetime.fromtimestamp(created_ts)

    def check_existing_file_date(self, **kwargs):
        # Load variables
        topic_id = kwargs.get("topic_id")
        thread_date = kwargs.get("thread_date")
        thread_url = kwargs.get("thread_url")

        # Check existing file date
        existing_file_date = self.get_existing_file_date(topic_id)
        if existing_file_date and existing_file_date > thread_date:
            self.logger.info(
                f"Thread {thread_url} ignored because existing "
                f"file is already latest. Last Scraped: {existing_file_date}"
            )
            return True

        return False

    def load_cookies(self, cookies_string):
        """
        :param cookies_string: str => Cookie string as in browser header
        :return: dict => Cookies as dict type, using in scrapy request
        """
        cookies_elements = [
            element.strip().split("=") for element in cookies_string.split(";")
        ]
        cookies = {
            element[0]: "=".join(element[1:]) for element in cookies_elements
        }
        return cookies

    def start_requests(self):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """
        if self.start_date and self.sitemap_url:
            yield scrapy.Request(
                url=self.sitemap_url,
                headers=self.headers,
                callback=self.parse_sitemap,
                dont_filter=True,
                meta={
                    "cookiejar": uuid.uuid1().hex
                }
            )
        else:
            yield Request(
                url=self.base_url,
                headers=self.headers,
                dont_filter=True
            )

    def parse_sitemap(self, response):
        """
        :param response: scrapy response => Level 1, forum sitemap
        :return:
        """

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load selector
        selector = Selector(text=response.text)

        # Load forum
        all_forum = selector.xpath(self.forum_sitemap_xpath).extract()

        for forum in all_forum:
            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_sitemap_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_sitemap_forum(self, response):
        """
        :param response: scrapy response => Level 2, thread sitemap
        :return:
        """

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load selector
        selector = Selector(text=response.text)

        # Load thread
        all_threads = selector.xpath(self.thread_sitemap_xpath).extract()

        for thread in all_threads:
            yield from self.parse_sitemap_thread(
                thread,
                response
            )

    def parse_sitemap_thread(self, thread, response):
        """
        :param thread: str => thread html include url and last mod
        :param response: scrapy response => scrapy response
        :return:
        """

        # Load selector
        selector = Selector(text=thread)

        # Load thread url and update
        thread_url = self.parse_thread_url(
            selector.xpath(self.thread_url_xpath).extract_first()
        )
        if not thread_url:
            return
        thread_date = self.parse_thread_date(
            selector.xpath(self.thread_lastmod_xpath).extract_first()
        )

        if self.start_date > thread_date:
            self.logger.info(
                "Thread %s ignored because last update in the past. Detail: %s" % (
                    thread_url,
                    thread_date
                )
            )
            return

        # Get topic id
        topic_id = self.get_topic_id(thread_url)
        if not topic_id:
            return

        # Check file exist
        if self.check_existing_file_date(
            topic_id=topic_id,
            thread_date=thread_date,
            thread_url=thread_url
        ):
            return

        # Load request arguments
        request_arguments = {
            "url": thread_url,
            "headers": self.headers,
            "callback": self.parse_thread,
            "meta": self.synchronize_meta(
                response,
                default_meta={
                    "topic_id": topic_id
                }
            )
        }
        if self.cookies:
            request_arguments["cookies"] = self.cookies

        yield Request(**request_arguments)

    def parse_forum(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "Next_page_url: %s" % response.url
        )

        threads = response.xpath(self.thread_xpath).extract()
        lastmod_pool = []

        for thread in threads:
            thread_url, thread_lastmod = self.extract_thread_stats(thread)

            if self.start_date and thread_lastmod is None:
                self.logger.info(
                    "Thread %s has no last update in update scraping, so ignored." % thread_url
                )
                continue

            lastmod_pool.append(thread_lastmod)

            # If start date, check last mod
            if self.start_date and thread_lastmod < self.start_date:
                self.logger.info(
                    "Thread %s last updated is %s before start date %s. Ignored." % (
                        thread_url, thread_lastmod, self.start_date
                    )
                )
                continue

            # Standardize thread url
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url

            # Parse topic id
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                continue

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                # -----------This is for quick test------------
                # return
                continue

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        # Pagination
        if not lastmod_pool:
            self.logger.info(
                "Forum without thread, exit."
            )
            return

        if self.start_date and self.start_date > max(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. Exit." % (
                    self.start_date,
                    response.url
                )
            )
            return

        next_page = response.xpath(self.pagination_xpath).extract_first()
        if next_page:
            if self.base_url not in next_page:
                next_page = self.base_url + next_page
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Load all post date
        post_dates = [
            self.parse_post_date(post_date) for post_date in
            response.xpath(self.post_date_xpath).extract()
            if post_date.strip()
        ]
        if self.start_date and max(post_dates) < self.start_date:
            self.logger.info(
                "No more post to update."
            )
            return

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # Save thread content
        if not self.useronly:
            current_page = response.xpath(
                self.thread_page_xpath
            ).extract_first() or "1"
            with open(
                file=os.path.join(
                    self.output_path,
                    "%s-%s.html" % (
                        topic_id,
                        current_page
                    )
                ),
                mode="w+",
                encoding="utf-8"
            ) as file:
                file.write(response.text)
                self.logger.info(
                    f'{topic_id}-{current_page} done..!'
                )

        # Thread pagination
        next_page = response.xpath(self.thread_pagination_xpath).extract_first()
        if next_page:

            if self.base_url not in next_page:
                next_page = self.base_url + next_page

            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = response.xpath(self.avatar_xpath).extract()
        for avatar_url in all_avatars:

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )

    def parse_avatar(self, response):

        # Load file name
        file_name = response.meta.get("file_name")
        avatar_name = os.path.basename(file_name)

        # Save avatar
        with open(file_name, "wb") as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar {avatar_name} done..!"
            )

    def parse_captcha(self, failure):
        # Load response, request
        response = failure.value.response
        request = failure.request

        # Load status
        status = getattr(response, "status", None)

        if (status == 403 and "Cloudfare" not in response.text):
            with open(file="captcha_debug.html", mode="w+", encoding="utf-8") as file:
                file.write(response.text)

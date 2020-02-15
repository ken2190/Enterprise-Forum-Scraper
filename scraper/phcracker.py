import re
import uuid

from datetime import datetime
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.3
NO_OF_THREADS = 10

USER = 'Cyrax_011'
PASS = 'c2Yv9EP8MsgGHJr'


class PHCrackerSpider(SitemapSpider):
    name = 'phcracker_spider'

    # Url stuffs
    base_url = "https://www.phcracker.net/"
    login_url = "https://www.phcracker.net/login/login"

    # Css stuffs
    login_form_css = "form[action*=login]"

    # Xpath stuffs
    forum_xpath = '//h3[@class="node-title"]/a/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = '//div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = '//span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = '//time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/(\d+)/",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*/page-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    handle_httpstatus_list = [503]
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        return datetime.strptime(
            thread_date.strip()[:-6],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-5],
            self.post_datetime_format
        )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_login
        )

    def parse_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "_xfRedirect": "https://www.phcracker.net/forums/-/list",
                "remember": "1",
                "login": USER,
                "password": PASS
            },
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_main_page
        )

    def parse_main_page(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class PHCrackerScrapper(SiteMapScrapper):

    spider_class = PHCrackerSpider
    site_name = 'phcracker.net'

    def load_settings(self):
        spider_settings = super().load_settings()
        return spider_settings

import os
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

#USERNAME = "thecreator101@protonmail.com"
#PASSWORD = "Night#Bhf01"
USERNAME = "vrx9@protonmail.com"
PASSWORD = "Vr#Bhf987"

class BHFIOSpider(SitemapSpider):

    name = 'bhfio_spider'

    # Url stuffs
    base_url = 'https://bhf.io'
    login_url = 'https://bhf.io/login/login'
    start_urls = ["https://bhf.io/"]

    # Regex stuffs
    topic_pattern = re.compile(r'threads/(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)')

    # Css stuffs
    login_form_css = "form[action]"
    backup_code_css = "a[href*=\"provider=backup\"]::attr(href)"
    account_css = r'a[href="/account/"]'

    # Xpath stuffs
    forum_xpath = "//a[contains(@href,\"/forums\")]/@href"
    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"
    thread_xpath = "//div[contains(@class,\"structItem--thread\")]"
    thread_first_page_xpath = "//div[@class=\"structItem-title\"]/a/@href"
    thread_last_page_xpath = "//span[@class=\"structItem-pageJump\"]/a[last()]/@href"
    thread_date_xpath = "//time[contains(@class,\"structItem-latestDate\")]/@title"
    thread_pagination_xpath = "//a[contains(@class,\"pageNav-jump--prev\")]/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]/a/text()"
    post_date_xpath = "//div[@class=\"message-attribution-main\"]/a[@class=\"u-concealed\"]/time/@title"

    avatar_xpath = "//img[contains(@class,\"avatar\")]/@src"

    # Other settings
    use_proxy = True
    sitemap_datetime_format = "%b %d, %Y at %I:%M %p"
    post_datetime_format = "%b %d, %Y at %I:%M %p"
    download_delay = 0.3
    download_thread = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update headers
        self.headers.update(
            {
                'referer': 'https://bhf.io/',
            }
        )

        # Load backup codes
        self.backup_code_file = os.path.join(
            os.getcwd(),
            "code/%s" % self.name
        )
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

    def start_requests(self):
        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response=response,
            formcss=self.login_form_css,
            formdata={
                "login": USERNAME,
                "password": PASSWORD
            },
            dont_filter=True,
            callback=self.parse_post_login,
            headers=self.post_headers,
            meta=self.synchronize_meta(response)
        )

    def parse_post_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load backup code url
        backup_code_url = "%s%s" % (
            self.base_url,
            response.css(self.backup_code_css).extract_first()
        )

        yield Request(
            url=backup_code_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_backup_code,
            meta=self.synchronize_meta(response)
        )

    def parse_backup_code(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load backup code
        code = self.backup_codes[0]
        self.backup_codes = self.backup_codes[1:]

        yield FormRequest.from_response(
            response=response,
            formcss=self.login_form_css,
            formdata={
                "code": code.replace(" ", ""),
                "trust": "0",
                "remember": "0"
            },
            meta=self.synchronize_meta(
                response,
                default_meta={
                    "backup_code_url": response.request.url,
                    "code": code
                }
            ),
            dont_filter=True,
            callback=self.parse_post_backup_code
        )

    def parse_post_backup_code(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load cookiejar
        cookiejar = response.meta.get("cookiejar")

        # Load ip
        ip = response.meta.get("ip")

        # Load backup code
        backup_code_url = response.meta.get("backup_code_url")

        # Load code
        code = response.meta.get("code")

        # Load account
        account = response.css(self.account_css).extract_first()

        # If not account and no more backup codes, return
        if not account and not self.backup_codes:
            self.logger.info(
                "None of backup code work."
            )
            self.write_backup_codes()
            return

        # If not account, try other code
        if not account:
            self.logger.info(
                "Code %s failed." % code
            )
            yield Request(
                url=backup_code_url,
                headers=self.headers,
                dont_filter=True,
                callback=self.parse_backup_code,
                meta=self.synchronize_meta(response)
            )
            return

        # If account, success
        self.logger.info(
            "Code %s success." % code
        )
        yield from super().start_requests(
            cookiejar=cookiejar,
            ip=ip
        )
        self.write_backup_codes()

    def get_topic_id(self, url=None):
        topic_id = self.topic_pattern.findall(url)
        try:
            return topic_id[0]
        except Exception as err:
            return

    def parse_thread_url(self, thread_url):
        return thread_url.replace(".vc", ".io")

    def parse(self, response):

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
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class BHFIOScrapper(SiteMapScrapper):

    spider_class = BHFIOSpider
    request_delay = 0.8
    no_of_threads = 4
    site_name = 'bhf.io'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )
        return spider_settings


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

import re
from datetime import datetime

import dateparser as dateparser
from scrapy import Request, FormRequest

from scraper.base_scrapper import SitemapSpiderWithDelay, SiteMapScrapperWithDelay

LOGINS = [
    {"USER": "Firefly13", "PASS": "X$$-Fl71hf7jsos2"},
    {"USER": "blackchain", "PASS": "BlackX$$19P1781jh"},
    {"USER": "SilverData", "PASS": "NewX$$_P127ds7"}
]

MIN_DELAY = 1
MAX_DELAY = 3

PROXY = 'http://127.0.0.1:8118'


class XSSSpider(SitemapSpiderWithDelay):
    name = "xss_spider"

    # DELAYS in SECONDS
    DELAY_BETWEEN_FORUMS = 600
    DELAY_FOR_FORUM_NEXT_PAGE = 200
    DELAY_BETWEEN_THREADS = 20
    DELAY_FOR_THREAD_NEXT_PAGE = 5
    DELAY_FOR_THREAD_PAGE_AVATARS = 1

    # Url stuffs
    base_url = "http://xssforumv3isucukbxhdhwz67hoa5e2voakcfkuieq4ch257vsburuid.onion/"
    login_url = f"{base_url}login/login"

    # Selectors
    login_form_xpath = "//form[@action='/login/login']"
    forum_xpath = '//h3[@class="node-title"]/a/@href|' \
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    forum_block_xpath = '//div[@data-node-id]//div[child::div[@class="node-body"]]'
    forum_block_date_xpath = './/time/@data-time'
    forum_block_url_xpath = './/h3[@class="node-title"]/a[starts-with(@href,"/forum")]/@href|' \
                            './/a[contains(@class,"subNodeLink--forum") and starts-with(@href,"/forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]' \
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]' \
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]' \
                        '/@data-time'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]' \
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]' \
                        '/a/text()'
    post_date_xpath = '//div[contains(@class, "message-cell--main")]//a/time[@datetime]/@data-time'
    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # captcha success
    bypass_success_xpath = '//div[contains(@class,"xb")]'

    # regexps
    topic_pattern = re.compile(r"threads/(\d+)/", re.IGNORECASE)
    avatar_name_pattern = re.compile(r".*/(\S+\.\w+)", re.IGNORECASE)
    pagination_pattern = re.compile(r".*page-(\d+)$", re.IGNORECASE)

    # Other settings
    use_proxy = "Tor"

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "blockMessage")]'
    retry_count = 0
    handle_httpstatus_list = [403, 501, 503]

    def start_requests(self, cookiejar=None, ip=None):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_start,
            meta={
                'proxy': PROXY,
            },
            dont_filter=True,
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        if not self.base_url in response.url or not response.text:
            yield from self.start_requests()
            return
        if not response.xpath(self.login_form_xpath):
            yield response.follow(
                url=self.base_url,
                headers=self.headers,
                callback=self.check_if_logged_in,
                meta=self.synchronize_meta(response),
                dont_filter=True,
            )
            return
        login = self.get_login(LOGINS)
        print(login)
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "login": login["USER"],
                "password": login["PASS"]
            },
            headers=self.headers,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            callback=self.check_if_logged_in
        )

    def check_if_logged_in(self, response):
        # check if logged in successfully
        if not self.base_url in response.url or not response.text:
            yield from self.start_requests()
            return
        if response.xpath(self.forum_xpath):
            # start forum scraping
            yield from self.parse(response)
            return
        err_msg = response.css('div.blockMessage--error::text').get() or 'Unknown error'
        self.logger.error('Unable to log in: %s', err_msg)
        if self.retry_count < 3:
            self.retry_count += 1
            self.logger.error(f"Retry #{self.retry_count+1}: Error logging in. Retrying...")
            yield from self.retry_request(response)
            return
        super().check_if_logged_in(response)

    def retry_request(self, response):
        yield Request(
            url=self.base_url,
            headers=self.synchronize_headers(response),
            callback=self.check_if_logged_in,
            meta=self.synchronize_meta(response),
            dont_filter=True,
        )

    def parse_thread(self, response):
        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        if thread_date is None:
            return None
        try:
            return datetime.fromtimestamp(float(thread_date))
        except:
            try:
                return datetime.strptime(
                    thread_date.strip(),
                    self.post_datetime_format
                )
            except:
                return dateparser.parse(thread_date).replace(tzinfo=None)

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        if post_date is None:
            return None
        try:
            return datetime.fromtimestamp(float(post_date))
        except:
            try:
                return datetime.strptime(
                    post_date.strip(),
                    self.post_datetime_format
                )
            except:
                return dateparser.parse(post_date).replace(tzinfo=None)

    def extract_all_forums(self, response):
        all_forum_blocks = response.xpath(self.forum_block_xpath)
        all_forum_urls = []
        for forum_block in all_forum_blocks:
            forum_block_date = forum_block.xpath(self.forum_block_date_xpath).extract_first()
            forum_lastmod = self.parse_thread_date(forum_block_date)
            forum_urls = forum_block.xpath(self.forum_block_url_xpath).extract()
            if self.start_date and forum_lastmod and forum_lastmod < self.start_date:
                self.logger.info(
                    f"Forum {forum_urls} last updated is {forum_lastmod} "
                    f"before start date {self.start_date}. Ignored.")
                continue
            all_forum_urls.extend(forum_urls)
        return set(all_forum_urls)


class XSSScrapper(SiteMapScrapperWithDelay):
    spider_class = XSSSpider
    site_name = 'xss.is'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'HTTPERROR_ALLOWED_CODES': [403],
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings

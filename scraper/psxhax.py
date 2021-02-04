import uuid
import re

from scrapy import (
    Request,
    FormRequest
)

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USER = 'Cyrax011'
PASS = 'Night#PSxHAx000'


class PsxhaxSpider(SitemapSpider):
    name = 'psxhax_spider'

    # Url stuffs
    base_url = "https://www.psxhax.com"
    forum_url = "https://www.psxhax.com/forums"
    login_url = "https://www.psxhax.com/login"

    # Css stuffs
    login_form_css = "form[action*=login]"

    # Xpath stuffs
    forum_xpath = '//h3[@class="node-title"]/a/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//a/span[@class="u-concealed" and @title]/text()'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "blockMessage blockMessage--error")]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"(?<=\.)\d*?(?=\/)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%S'
    post_datetime_format = '%b %d, %Y at %I:%M %p'

    def parse_thread_date(self, thread_date):
        return super().parse_thread_date(thread_date.strip()[:-5])

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "login": USER,
                "password": PASS,
                "_xfRedirect": "/"
            },
            meta=self.synchronize_meta(response),
            dont_filter=True,
            callback=self.parse_login
        )

    def parse_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        yield Request(
            url=self.forum_url,
            headers=self.headers,
            callback=self.parse_start,
            meta=self.synchronize_meta(response)
        )

    def parse_start(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:
            # Standardize forum url
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


class PsxhaxScrapper(SiteMapScrapper):

    spider_class = PsxhaxSpider
    site_name = 'psxhax.com'
    site_type = 'forum'

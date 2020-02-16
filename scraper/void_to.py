import re
import os

from datetime import datetime, timedelta

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = .3
NO_OF_THREADS = 12
USERNAME = "night_cyrax"
PASSWORD = "a63ffcb44e1a11eaa087b42e994a598f"


class VoidToSpider(SitemapSpider):

    name = "void_to"

    # Url stuffs
    base_url = "https://void.to/"
    login_url = "https://void.to/member.php?action=login"

    # Css stuffs
    login_form_css = 'form[action="member.php"]'

    # Xpath stuffs

    # Forum xpath #
    forum_xpath = '//span[@class="forum-name-display"]'\
                  '/a[contains(@href, "Forum-") or contains'\
                  '(@href, "forumdisplay.php")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[contains(@class,"pagination_next")]/@href'

    # Thread xpath #
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//a[@class="topic-title"]/@href'
    topic_last_page_xpath = '//a[@class="pagination_last"]/@href'
    thread_date_xpath = '//span[@class="last-post-date"]/text()'
    thread_pagination_xpath = '//span[@class="pagination_current"]/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'

    # Post xpath #
    post_date_xpath = '//span[@class="post_date"]/descendant::text()'
    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@class="g-recaptcha"]/@data-sitekey'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )
    days_ago_pattern = re.compile(
        r'(\d+) days ago',
        re.IGNORECASE
    )
    months_ago_pattern = re.compile(
        r'(\d+) months ago',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%b %d, %Y'
    sitemap_datetime_format = '%b %d, %Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()
        today = ['hour', 'minute', 'second']

        if any(v in thread_date.lower() for v in today):
            return datetime.today()
        elif 'yesterday' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        elif self.days_ago_pattern.match(thread_date.lower()):
            days_ago = self.days_ago_pattern.findall(thread_date.lower())[0]
            return datetime.today() - timedelta(days=int(days_ago))
        elif 'last month' in thread_date.lower():
            return datetime.today() - timedelta(days=30)
        elif self.months_ago_pattern.match(thread_date.lower()):
            months_ago = self.months_ago_pattern.findall(thread_date.lower())[0]
            return datetime.today() - timedelta(days=30*int(months_ago))
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        post_date = post_date.strip()
        today = ['hour', 'minute', 'second']

        if any(v in post_date.lower() for v in today):
            return datetime.today()
        elif 'yesterday' in post_date.lower():
            return datetime.today() - timedelta(days=1)
        elif self.days_ago_pattern.match(post_date.lower()):
            days_ago = self.days_ago_pattern.findall(post_date.lower())[0]
            return datetime.today() - timedelta(days=int(days_ago))
        elif 'last month' in post_date.lower():
            return datetime.today() - timedelta(days=30)
        elif self.months_ago_pattern.match(post_date.lower()):
            months_ago = self.months_ago_pattern.findall(post_date.lower())[0]
            return datetime.today() - timedelta(days=30*int(months_ago))
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            meta=self.synchronize_meta(response)
        )

    def parse_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "username": USERNAME,
                "password": PASSWORD,
                "remember": "yes",
                "submit": "Login",
                "action": "do_login",
                "url": "",
                "g-recaptcha-response": self.solve_recaptcha(response)
            },
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            # Add sort lastest
            forum_url = forum_url + "?sortMode=lastest"

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check current page and last page
        current_page = response.xpath(self.thread_page_xpath).extract_first()
        last_page = response.xpath(self.topic_last_page_xpath).extract_first()

        # Reverse scraping start here
        if current_page == 1 and last_page:
            yield Request(
                url=last_page,
                headers=self.headers,
                callback=super().parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": response.meta.get("topic_id")
                    }
                )
            )

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class VoidToScrapper(SiteMapScrapper):

    spider_class = VoidToSpider


if __name__ == '__main__':
    pass

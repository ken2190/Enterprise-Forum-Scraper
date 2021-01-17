import re
import os
import uuid

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


USERNAME = "crhz"
PASSWORD = "4hr63yh38a61SDW0"


class CrackingKingSpider(SitemapSpider):

    name = "crackingking"

    # Url stuffs
    base_url = "https://crackingking.com/"
    login_url = "https://crackingking.com/member.php?action=login"

    # Css stuffs
    login_form_css = "form[action]"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="smalltext"]/text()[1]|'\
                      '//span[@class="smalltext"]/span/@title'\

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//tr[contains(text(), "You have failed to login within")]'

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@class="g-recaptcha"]/@data-sitekey'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*thread-(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
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
    use_proxy = True
    handle_httpstatus_list = [503]
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()
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
        post_date = post_date.split(',')[0].strip()
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

    def start_requests(self,):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        formdata = {
            "username": USERNAME,
            "password": PASSWORD,
            "remember": "yes",
            "submit": "Login",
            "action": "do_login",
            "url": f'{self.base_url}index.php',
            "g-recaptcha-response": self.solve_recaptcha(response)
        }

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata=formdata,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            if 'forum-146' not in forum_url:
                continue

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class CrackingKingScrapper(SiteMapScrapper):

    spider_class = CrackingKingSpider
    site_name = 'crackingking.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

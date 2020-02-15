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
    recaptcha_site_key_xpath = '//div[@class="g-recaptcha"]/@data-sitekey'
    forum_xpath = '//span[@class="forum-name-display"]'\
                  '/a[contains(@href, "Forum-") or contains'\
                  '(@href, "forumdisplay.php")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[contains(@class,"pagination_next")]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = '//a[@class="topic-title"]/@href'
    thread_last_page_xpath = '//a[@class="pagination_last"]/@href'
    thread_date_xpath = '//span[@class="last-post-date"]/text()'
    thread_pagination_xpath = '//span[@class="pagination_current"]'\
                              '/preceding-sibling::a[@class="pagination_page"'\
                              '][1]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/descendant::text()'

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'
    post_datetime_format = '%b %d, %Y'
    sitemap_datetime_format = '%b %d, %Y'

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
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

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
            # if 'Forum-Other-Cheats' not in forum_url:
            #     continue

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def extract_thread_stats(self, thread):
        selector = Selector(text=thread)

        thread_lastmod = selector.xpath(
            self.thread_date_xpath
        ).extract_first()

        thread_url = selector.xpath(
            self.thread_first_page_xpath
        ).extract_first()

        try:
            thread_url = thread_url.strip()
        except Exception as err:
            thread_url = None

        try:
            thread_lastmod = self.parse_thread_date(thread_lastmod)
        except Exception as err:
            thread_lastmod = None

        return thread_url, thread_lastmod

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
                callback=self.parse_thread_last_url,
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

    def parse_thread_last_url(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        last_url = response.xpath(self.thread_last_page_xpath).extract_first()
        if not last_url:
            # Save generic thread
            yield from super().parse_thread(response)

            # Save avatars
            yield from super().parse_avatars(response)
        else:
            # Get topic id
            topic_id = response.meta.get("topic_id")
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
            # Standardize url
            if self.base_url not in last_url:
                last_url = self.base_url + last_url
            yield Request(
                url=last_url.strip(),
                headers=self.headers,
                callback=self.parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)

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


class VoidToScrapper(SiteMapScrapper):

    spider_class = VoidToSpider

    def load_settings(self):
        settings = super().load_settings()
        return settings


if __name__ == '__main__':
    pass

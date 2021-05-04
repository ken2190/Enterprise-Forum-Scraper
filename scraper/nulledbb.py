import os
import re

import dateutil.parser as dparser
from scrapy import Request, FormRequest

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = ""
PASSWORD = ""


class NulledBBSpider(SitemapSpider):
    name = 'nulledbb_spider'

    # Url stuffs
    base_url = "https://nulledbb.com/"
    login_url = f"{base_url}login"
    search_url = f"{base_url}search"
    start_urls = ["https://nulledbb.com/"]

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r'.*avatar_(\d+\.\w+)',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )

    # Xpath stuffs
    forum_xpath = '//section[contains(@class, "subforums")]//li[contains(@class, "mb-1")]/a/@href |' \
                  '//section[contains(@class, "forumdisplay-subforum")]//div[contains(@class, "forum-title")]/a/@href'

    thread_xpath = '//div[@class="content"]//div[contains(@class,"main-row") and contains(@class,"d-flex")]'
    pagination_xpath = '//a[contains(@class, "pagination_next")]/@href'
    thread_last_page_xpath = './/a[text()="Last Post"]/@href'
    thread_date_xpath = './/a[text()="Last Post"]/preceding-sibling::div//span/@title|' \
                        './/a[text()="Last Post"]/preceding-sibling::div/*/text()'
    login_form_xpath = '//form[@action="member.php"]'
    search_form_xpath = '//form[@action="search.php"]'
    last_page_xpath = '//div[contains(@class, "pagination")]//ul/li[last()]/a/@href'

    avatar_xpath = '//a[contains(@class, "post-avatar")]/img/@src'

    thread_page_xpath = '//a[contains(@class,"pagination_current")]/text()'

    thread_pagination_xpath = '//a[contains(@class, "pagination_previous")]/@href'

    post_date_xpath = '//div[@class="flex-fill"]/span[@data-toggle="tooltip"]/span/@title|' \
                      '//div[@class="flex-fill"]/span[@data-toggle="tooltip"]/text()'

    thread_date_pattern = ""

    post_datetime_format = "%d-%m-%Y, %I:%M %p"
    thread_datetime_format = "%d-%m-%Y, %I:%M %p"

    use_proxy = "On"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://nulledbb.com/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1"
            }
        )

    def start_requests(self, cookiejar=None, ip=None):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load meta
        meta = {}
        if cookiejar:
            meta["cookiejar"] = cookiejar
        if ip:
            meta["ip"] = ip

        # Login if username is present
        if USERNAME:
            yield Request(
                url=self.login_url,
                headers=self.headers,
                errback=self.check_site_error,
                callback=self.login_to_site,
                dont_filter=True,
                meta=meta
            )
        else:
            yield Request(
                url=self.search_url,
                headers=self.headers,
                errback=self.check_site_error,
                callback=self.search_unread_posts,
                dont_filter=True,
                meta=meta
            )

    def login_to_site(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        my_post_key = response.xpath(
            '//input[@name="my_post_key"]/@value').extract_first()
        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
            'remember': 'yes',
            'action': 'do_login',
            'url': "/member.php",
            'my_post_key': my_post_key,
        }

        print(formdata)
        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.check_login_and_redirect
        )

    def check_login_and_redirect(self, response):
        self.synchronize_headers(response)

        self.check_if_logged_in(response)

        yield Request(
            url=self.search_url,
            headers=self.headers,
            errback=self.check_site_error,
            callback=self.search_unread_posts,
            dont_filter=True,
            meta=self.synchronize_meta(response)
        )

    def search_unread_posts(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        formdata = {
            'action': 'do_search',
            'keywords': '',
            'postthread': '1',
            'forums[]': 'all',
            'author': '',
            'matchusername': '1',
            'findthreadst': '1',
            'numreplies': '',
            'postdate': '0',
            'pddir': '1',
            'threadprefix[]': 'any',
            'sortby': 'lastpost',
            'sortordr': 'desc',
            'showresults': 'threads',
            'submit': 'Search'
        }
        yield FormRequest.from_response(
            response=response,
            formxpath=self.search_form_xpath,
            formdata=formdata,
            headers=self.headers,
            dont_filter=True,
            meta=self.synchronize_meta(response),
            callback=self.navigate_unread_posts
        )

    def extract_thread_stats(self, thread):
        """
        :param thread: str => thread html contain url and last mod
        :return: thread url: str, thread lastmod: datetime
        """
        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            ).extract_first()

        thread_lastmod = thread.xpath(
            self.thread_date_xpath
        ).extract_first()

        # Process stats
        if thread_last_page_url:
            thread_url = thread_last_page_url.strip()
        else:
            thread_url = None

        try:
            if 'seconds ago' in thread_lastmod:
                seconds = thread_lastmod.split(' ')[0]
                thread_lastmod_parsed = datetime.datetime.now() - datetime.timedelta(seconds=-int(seconds))
            else:
                thread_lastmod_parsed = dparser.parse(thread_lastmod.strip(), dayfirst=True)
        except Exception:
            thread_lastmod_parsed = None
        return thread_url, thread_lastmod_parsed

    def navigate_unread_posts(self, response, thread_meta={}, is_first_page=True):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "Next_page_url: %s" % response.url
        )

        threads = response.xpath(self.thread_xpath)
        lastmod_pool = []
        for thread in threads:
            thread_url, thread_lastmod = self.extract_thread_stats(thread)
            if not thread_url:
                self.crawler.stats.inc_value("mainlist/detail_no_url_count")
                self.logger.warning(
                    "Unable to find thread URL on the forum: %s",
                    response.url
                )
                continue

            # Parse topic id
            topic_id = self.get_topic_id(thread_url)

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                thread_url = temp_url

            # Check file exist
            if self.check_existing_file_date(
                    topic_id=topic_id,
                    thread_date=thread_lastmod,
                    thread_url=thread_url
            ):
                # update stats
                if topic_id not in self.topics:
                    self.topics.add(topic_id)
                    self.crawler.stats.inc_value("mainlist/detail_already_scraped_count")
                    self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

                continue

            # Check thread meta
            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)

            # Update topic id
            meta["topic_id"] = str(topic_id)

            # update stats
            self.topics.add(topic_id)
            self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
            )

        # Pagination
        if not lastmod_pool:
            self.crawler.stats.inc_value("mainlist/mainlist_no_detail_count")
            self.logger.info(
                "Forum without thread, exit: %s",
                response.url
            )
            return

        if self.start_date and self.start_date > min(lastmod_pool):
            self.logger.info(
                "Found no more thread update later than %s in forum %s. Exit." % (
                    self.start_date,
                    response.url
                )
            )
            return

        # get next page
        next_page = self.get_forum_next_page(response)
        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.navigate_unread_posts,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def process_thread(self, response):
        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        thread_last_page_url = response.xpath(
            self.last_page_xpath
        ).extract_first()

        if thread_last_page_url:
            thread_last_page_url = self.parse_thread_url(thread_last_page_url)

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_last_page_url and 'https://' not in thread_last_page_url:
                temp_url = thread_last_page_url
                if self.base_url not in thread_last_page_url:
                    temp_url = response.urljoin(thread_last_page_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_last_page_url

                thread_last_page_url = temp_url
        else:
            thread_last_page_url = response.url

        yield Request(
            url=thread_last_page_url,
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

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # Load all post date
        post_dates = [
            self.parse_post_date(post_date) for post_date in
            response.xpath(self.post_date_xpath).extract()
            if post_date.strip() and self.parse_post_date(post_date)
        ]

        if self.start_date and not post_dates:
            self.logger.info('No dates found in thread: %s', response.url)
            return

        # get next page
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.crawler.stats.inc_value("mainlist/detail_next_page_count")

        # check if the thread contains new messages
        if self.start_date and max(post_dates) < self.start_date:
            if topic_id not in self.topics_scraped:
                self.crawler.stats.inc_value("mainlist/detail_outdated_count")

            self.logger.info(
                "No more post to update."
            )
            return

        # Save thread content
        if not self.useronly:
            current_page = self.get_thread_current_page(response)
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

            # Update stats
            self.topics_scraped.add(topic_id)
            self.crawler.stats.set_value(
                "mainlist/detail_saved_count",
                len(self.topics_scraped)
            )

        # Thread pagination
        if next_page:
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

        yield from super().parse_avatars(response)


class NulledBBScrapper(SiteMapScrapper):
    spider_class = NulledBBSpider
    site_name = 'nulledbb.com'
    site_type = 'forum'

import re
import os
import hashlib
import time
import random
import traceback
from requests import Session
from lxml.html import fromstring

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    BaseScrapper,
    SitemapSpider,
    SiteMapScrapper
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"

# Credentials
USERNAME = "Dexter"
PASSWORD = "Dig#DexNum#1"

PROXY = 'http://127.0.0.1:8118'
DAILY_LIMIT = 10000
MIN_DELAY = 5
MAX_DELAY = 30

class KickAssSpider(SitemapSpider):
    name = "kickass_spider"
    base_url = "http://qoodvrvo2dq72sygqrvm4ymx2zwojplom4m6giiggobf3dpt5up24did.onion/"
    start_url = f"{base_url}index.php"
    login_url = f"{base_url}member.php"
    # topic_url = f"{base_url}showthread.php?tid={}"

    # xpath stuffs
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = "//ul[contains(@class, user_links)]//a[contains(@href, 'search.php?action=unreads')]/@href"

    pagination_xpath = "//a[@class='pagination_next']/@href"
    thread_xpath = "//table[contains(@class, 'tborder')]//tr[contains(@class, 'inline_row')]"
    thread_first_page_xpath = ".//span/a[contains(@id,'tid_')]/@href"

    thread_last_page_xpath = './/span/span[contains(@class,"smalltext")]/a[contains(@href, "tid=")][last()]/@href'

    thread_pagination_xpath = "//a[@class='pagination_previous']/@href"
    thread_page_xpath = "//span[contains(@class,'pagination_current')]/text()"
    
    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    login_failed_xpath = '//span[text()="Incorrect username and/or password."]'

    ignore_xpath = '//td[contains(text(), "The specified thread does not exist")]'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*avatar_(\d+\.\w+)\?",
        re.IGNORECASE
    )

    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )
    
    use_proxy = "Tor"
    RAMDOM_REQUEST_COUNT = random.randint(5, 10)
    RAMDOM_AVATAR_REQUEST_COUNT = random.randint(5, 20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def extract_thread_stats(self, thread):
        """
        :param thread: str => thread html contain url and last mod
        :return: thread url: str, thread lastmod: datetime
        """
        # Load selector
        # selector = Selector(text=thread)

        # Load stats
        thread_first_page_url = None
        if self.thread_first_page_xpath:
            thread_first_page_url = thread.xpath(
                self.thread_first_page_xpath
            ).extract_first()

        thread_last_page_url = None
        if self.thread_last_page_xpath:
            thread_last_page_url = thread.xpath(
                self.thread_last_page_xpath
            ).extract_first()

        # Process stats
        try:
            thread_url = (self.parse_thread_url(thread_last_page_url)
                          or self.parse_thread_url(thread_first_page_url))
        except Exception as err:
            thread_url = None

        return thread_url

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def start_requests(self):
        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            errback=self.check_site_error,
            dont_filter=True,
            meta={
                'proxy': PROXY,
            }
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middleware
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
            callback=self.parse_redirect
        )

    def parse_redirect(self, response):

        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        yield Request(
            url=self.start_url,
            callback=self.parse_start,
            headers=response.request.headers,
            meta=self.synchronize_meta(response),
            dont_filter=True
        )

    def parse_start(self, response):

        self.synchronize_headers(response)
        
        unread_post_url = response.xpath(self.forum_xpath).extract_first()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", 1)
        if self.base_url not in unread_post_url:
            unread_post_url = response.urljoin(unread_post_url)

        yield Request(
            url=unread_post_url,
            headers=self.headers,
            callback=self.parse_unread_direct,
            meta=self.synchronize_meta(response)
        )

    def parse_unread_direct(self, response):
        self.synchronize_headers(response)

        redirect_url = response.xpath("//a[contains(@href, 'search.php?action=results')]/@href").extract_first()
        if self.base_url not in redirect_url:
            redirect_url = response.urljoin(redirect_url)
        
        yield Request(
            url=redirect_url,
            headers=self.headers,
            callback=self.parse_forum,
            meta=self.synchronize_meta(response)
        )

    def parse_forum(self, response, thread_meta={}, is_first_page=True):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        self.logger.info(
            "Next_page_url: %s" % response.url
        )

        threads = response.xpath(self.thread_xpath)

        for thread in threads:
            thread_url = self.extract_thread_stats(thread)
            if not thread_url:
                self.crawler.stats.inc_value("mainlist/detail_no_url_count")
                self.logger.warning(
                    "Unable to find thread URL on the forum: %s",
                    response.url
                )
                continue

            # Parse topic id
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                self.crawler.stats.inc_value("mainlist/detail_no_topic_id_count")
                self.logger.warning(
                    "Unable to find topic ID of the thread: %s",
                    response.urljoin(thread_url)
                )
                continue

            # Standardize thread url only if it is not complete url
            if 'http://' not in thread_url and 'https://' not in thread_url:
                temp_url = thread_url
                if self.base_url not in thread_url:
                    temp_url = response.urljoin(thread_url)

                if self.base_url not in temp_url:
                    temp_url = self.base_url + thread_url

                thread_url = temp_url

            # Check thread meta
            if thread_meta:
                meta = thread_meta
            else:
                meta = self.synchronize_meta(response)

            # Update topic id
            meta["topic_id"] = topic_id

            # update stats
            self.topics.add(topic_id)
            self.crawler.stats.set_value("mainlist/detail_count", len(self.topics))

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta=meta
            )

        # get next page
        next_page = self.get_forum_next_page(response)
        if is_first_page and next_page:
            self.crawler.stats.inc_value("mainlist/mainlist_next_page_count")

        # update stats
        if is_first_page:
            self.crawler.stats.inc_value("mainlist/mainlist_processed_count")

        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
                cb_kwargs={'is_first_page': False}
            )

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # get next page
        next_page = self.get_thread_next_page(response)
        if next_page:
            self.crawler.stats.inc_value("mainlist/detail_next_page_count")

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

            self.RAMDOM_REQUEST_COUNT = self.RAMDOM_REQUEST_COUNT - 1
            if self.RAMDOM_REQUEST_COUNT == 0:
                self.RAMDOM_REQUEST_COUNT = random.randint(5, 10)
                time.sleep(random.randint(60, 120))

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

        # Parse avatar
        yield from self.parse_avatars(response)
    
    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = set(response.xpath(self.avatar_xpath).extract())

        for avatar_url in all_avatars:
            # Standardize avatar url only if its not complete url
            slash = False
            if 'http://' not in avatar_url and 'https://' not in avatar_url:
                temp_url = avatar_url

                if avatar_url.startswith('//'):
                    slash = True
                    temp_url = avatar_url[2:]

                if not avatar_url.lower().startswith("http"):
                    temp_url = response.urljoin(avatar_url)

                if self.base_url not in temp_url and not slash:
                    temp_url = self.base_url + avatar_url

                avatar_url = temp_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            # update stats
            self.avatars.add(avatar_url)
            self.crawler.stats.set_value("mainlist/avatar_count", len(self.avatars))
            
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

        self.RAMDOM_AVATAR_REQUEST_COUNT = self.RAMDOM_AVATAR_REQUEST_COUNT - 1
        if self.RAMDOM_AVATAR_REQUEST_COUNT == 0:
            self.RAMDOM_AVATAR_REQUEST_COUNT = random.randint(5, 20)
            time.sleep(random.randint(30, 60))

        self.crawler.stats.inc_value("mainlist/avatar_saved_count")
        
class KickAssScrapper(SiteMapScrapper):

    spider_class = KickAssSpider
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "CLOSESPIDER_PAGECOUNT": DAILY_LIMIT,
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings

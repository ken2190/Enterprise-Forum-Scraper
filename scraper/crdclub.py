import os
import re
import uuid

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USER = 'Cyrax_011'
PASS = 'S5eVZWqf!3wNdtb'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'


class CrdClubSpider(SitemapSpider):
    name = "crdclub_spider"

    # Url stuffs
    base_url = "http://crdclub.su/"

    # Regex stuffs
    topic_pattern = re.compile(
        r't=(\d+)',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*u=(\w+)\&',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*page=(\d+)',
        re.IGNORECASE
    )

    # Xpath stuffs
    login_form_xpath = '//form[@action="login.php?do=login"]'
    forum_xpath = '//a[contains(@href, "forumdisplay.php?")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = './/span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]/text()'
    avatar_xpath = '//a[contains(@href, "member.php?")]/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(text(), "You have entered an invalid username or password")]'

    # Other settings
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y, %H:%M'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            'origin': 'https://crdclub.su',
            'referer': 'https://crdclub.su/index.php',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'user-agent': USER_AGENT,
        })

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

        formdata = {
            'vb_login_username': USER,
            'vb_login_password': PASS,
        }
        yield FormRequest.from_response(
            response=response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.after_login,
        )

    def after_login(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_start,
            meta=self.synchronize_meta(response),
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()
        if "today" in thread_date.lower():
            return datetime.today()
        elif "yesterday" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()
        if not post_date:
            return

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse_start(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
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

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class CrdClubScrapper(SiteMapScrapper):

    spider_class = CrdClubSpider
    site_name = 'crdclub.su'
    site_type = 'forum'

import os
import re
import scrapy
import uuid

from datetime import datetime

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USER = 'Exabyte'
PASS = 'Night#OG009'
REQUEST_DELAY = .6
NO_OF_THREADS = 20


class OgUsersSpider(SitemapSpider):

    name = 'ogusers_spider'

    # Url stuffs
    base_url = "https://ogusers.com/"
    login_url = "https://ogusers.com/member.php?action=login"

    # Css stuffs
    login_form_css = "#quick_login>form"
    forum_css = "td.col_row>a[href*=Forum-]::attr(href), " \
                "td.col_row>a[href*=Forum-] + div.smalltext>div>a[href*=Forum-]::attr(href)"

    # Xpath stuffs
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"
    thread_xpath = "//tr[contains(@class, \"thread_row\")]"
    thread_first_page_xpath = "//span[contains(@class,\"subject\")]/a[contains(@href,\"Thread-\")]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/span[@title]/@title|" \
                        "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]"
    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_last_xpath = "//div[@class=\"pagination\"]/a[@class=\"pagination_last\"]/@href|" \
                        "//div[@class=\"pagination\"]/a[@class=\"pagination_next\"]/preceding-sibling::a/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//div[@class=\"inline pb_date smalltext\"]/text()[contains(.,\"-\")]|" \
                      "//div[@class=\"inline pb_date smalltext\"]/span[@title]/@title"
    avatar_xpath = "//div[@class=\"postbit-avatar\"]/a/img/@src"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%m-%d-%Y"
    handle_httpstatus_list = [403]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {
            "Referer": "https://ogusers.com",
            "Sec-fetch-mode": "navigate",
            "Sec-fetch-site": "same-origin",
            "Sec-fetch-user": "?1",
        }

    def get_avatar_file(self, url):

        if "image/svg" in url:
            return

        return super().get_avatar_file(url)

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        if thread_date is None:
            return datetime.today()

        return datetime.strptime(
            thread_date.strip()[:10],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """

        if post_date is None:
            return datetime.today()

        return datetime.strptime(
            post_date.strip()[:10],
            self.sitemap_datetime_format
        )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            callback=self.parse,
        )

    def parse(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login,
            meta=self.synchronize_meta(response)
        )

    def parse_login(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "username": USER,
                "password": PASS,
                "2facode": "",
                "action": "do_login"
            },
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_start,
            meta=self.synchronize_meta(response)
        )

    def parse_start(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.css(self.forum_css).extract()
        for forum in all_forums:

            if self.base_url not in forum:
                forum = self.base_url + forum

            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load topic_id
        topic_id = response.meta.get("topic_id")

        # Check current page to scrape from last page
        current_page = response.xpath(self.thread_page_xpath).extract_first()
        last_page = response.xpath(self.thread_last_xpath).extract_first()
        if current_page == "1":

            if self.base_url not in last_page:
                last_page = self.base_url + last_page

            yield Request(
                url=last_page,
                headers=self.headers,
                callback=super().parse_thread,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "topic_id": topic_id
                    }
                )
            )

        # Parse main thread
        yield from super().parse_thread(response)

        # Parse avatar thread
        yield from super().parse_avatars(response)

        # Save user content
        users = response.xpath("//div[@class=\"postbitdetail\"]/span/a")
        for user in users:
            user_url = user.xpath("@href").extract_first()
            if self.base_url not in user_url:
                user_url = self.base_url + user_url
            user_name = user.xpath("span/text()").extract_first()
            if not user_name:
                user_name = user.xpath("text()").extract_first()
            if not user_name:
                user_name = user.xpath("font/text()").extract_first()
            file_name = '{}/{}.html'.format(self.user_path, user_name)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=user_url,
                headers=self.headers,
                callback=self.parse_user,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name,
                        "user_name": user_name,
                    }
                )
            )

    def parse_user(self, response):
        # Synchronize headers
        self.synchronize_headers(response)

        # Save user contents
        file_name = response.meta.get("file_name")
        user_name = response.meta.get("user_name")
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(
                f"User {user_name} done..!"
            )

        user_history = response.xpath(
            "//div[@class=\"usernamehistory\"]/a"
        )

        # Parse user history
        if user_history:
            history_url = user_history.xpath("@href").extract_first()

            if self.base_url not in history_url:
                history_url = self.base_url + history_url

            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "user_name": user_name,
                    }
                )
            )

    def parse_user_history(self, response):
        user_name = response.meta['user_name']
        file_name = '{}/{}-history.html'.format(self.user_path, user_name)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(
                f"History for user {user_name} done..!"
            )


class OgUsersScrapper(SiteMapScrapper):

    spider_class = OgUsersSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "DOWNLOAD_DELAY": REQUEST_DELAY,
                "CONCURRENT_REQUESTS": NO_OF_THREADS,
                "CONCURRENT_REQUESTS_PER_DOMAIN": NO_OF_THREADS,
            }
        )
        return settings

import os
import re
import scrapy

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
    thread_xpath = "//tr[contains(@class, \"thread_row\")]"
    thread_url_xpath = "//span[contains(@class,\"subject\")]/a[contains(@href,\"Thread-\")]/@href"
    thread_lastmod_xpath = "//span[@class=\"lastpost smalltext\"]/span[@title]/@title|" \
                           "//span[@class=\"lastpost smalltext\"]/br/following-sibling::text()"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    # Regex stuffs
    pagination_pattern = re.compile(r'.*page=(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%m-%d-%Y"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {
            "Referer": "https://ogusers.com",
            "Sec-fetch-mode": "navigate",
            "Sec-fetch-site": "same-origin",
            "Sec-fetch-user": "?1",
        }

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        if "seconds" in thread_date:
            return datetime.today()

        return datetime.strptime(
            thread_date.strip()[:10],
            self.sitemap_datetime_format
        )

    def parse(self, response):
        self.synchronize_headers(response)
        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login
        )

    def parse_login(self, response):
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
            callback=self.parse_start
        )

    def parse_start(self, response):

        self.synchronize_headers(response)
        all_forums = response.css(self.forum_css).extract()

        for forum in all_forums:

            if self.base_url not in forum:
                forum = self.base_url + forum

            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_forum
            )

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

            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={"topic_id": topic_id}
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
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Get topic id
        topic_id = response.meta.get("topic_id")

        # Save thread content
        if not self.useronly:
            pagination = self.pagination_pattern.findall(response.url)
            paginated_value = pagination[0] if pagination else 1
            file_name = '{}/{}-{}.html'.format(
                self.output_path, topic_id, paginated_value)
            with open(file_name, 'wb') as f:
                f.write(response.text.encode('utf-8'))
                self.logger.info(
                    f'{topic_id}-{paginated_value} done..!'
                )

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
                meta={
                    "file_name": file_name,
                    "user_name": user_name
                }
            )

        # Save avatar content
        avatars = response.xpath("//div[@class=\"postbit-avatar\"]/a/img")
        for avatar in avatars:
            avatar_url = avatar.xpath("@src").extract_first()
            if "image/svg" in avatar_url:
                continue
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    "file_name": file_name,
                }
            )

        # Thread pagination
        next_page = response.xpath(
            "//div[@class=\"pagination\"]//a[@class=\"pagination_next\"]"
        )
        if next_page:
            next_page_url = next_page.xpath("@href").extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={
                    "topic_id": topic_id
                }
            )

    def parse_user(self, response):
        self.synchronize_headers(response)
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
        if user_history:
            history_url = user_history.xpath("@href").extract_first()

            if self.base_url not in history_url:
                history_url = self.base_url + history_url

            yield Request(
                url=history_url,
                headers=self.headers,
                callback=self.parse_user_history,
                meta={
                    "user_name": user_name
                }
            )

    def parse_user_history(self, response):
        user_name = response.meta['user_name']
        file_name = '{}/{}-history.html'.format(self.user_path, user_name)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(
                f"History for user {user_name} done..!"
            )

    def parse_avatar(self, response):
        file_name = response.meta.get("file_name")
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar {file_name_only} done..!"
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

import re

from datetime import datetime

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = .3
NO_OF_THREADS = 12
USERNAME = "seraleone"
PASSWORD = "BcCeQGx5"


class SinisterSpider(SitemapSpider):

    name = "sinister"

    # Url stuffs
    base_url = "https://sinister.ly/"
    login_url = ""

    # Css stuffs
    forum_css = r"td>strong>a[href*=Forum-]::attr(href)"
    current_page_css = r".pagination_current::text"
    login_form_css = "form[action]"

    # Xpath stuffs
    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span/span[@class=\"smalltext\"]/a[contains(@href,\"Thread-\")][last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/span[@title]/@title|" \
                        "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"
    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date postbit_date\"]/text()[contains(.,\"-\")]|" \
                      "//span[@class=\"post_date postbit_date\"]/span[@title]/@title"
    avatar_xpath = "//div[@class=\"author_avatar postbit_avatar\"]/a/img/@src"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\w+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%m-%d-%Y"
    use_proxy = True

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
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
        return datetime.strptime(
            post_date.strip()[:10],
            self.post_datetime_format
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Login stuffs
        self.post_headers.update(self.headers)
        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "quick_username": USERNAME,
                "quick_password": PASSWORD,
                "url": "",
                "quick_login": "1",
                "action": "do_login",
                "submit": "Login",
            },
            dont_filter=True,
            headers=self.post_headers,
            callback=self.parse_start,
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.css(self.forum_css).extract()

        # Loop forums
        for forum in all_forums:

            # Standardize forum url
            if self.base_url not in forum:
                forum = "%s%s" % (
                    self.base_url,
                    forum
                )

            yield Request(
                url=forum,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):

        # Load sub forums
        current_page = response.css(self.current_page_css).extract_first()
        if current_page == "1":
            yield from self.parse_start(response)

        # Parse main forum
        yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Parse main thread
        yield from super().parse_thread(response)

        # Parse avatar
        yield from super().parse_avatars(response)


class SinisterScrapper(SiteMapScrapper):

    spider_class = SinisterSpider
    site_name = 'sinister.ly'

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


if __name__ == '__main__':
    pass

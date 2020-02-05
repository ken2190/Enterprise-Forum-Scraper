import os
import re

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


REQUEST_DELAY = 1
NO_OF_THREADS = 1
USER = "hackwithme123"
PASS = "6VUZmjFzM2WtyjV"


class V3RMillionSpider(SitemapSpider):
    name = "v3rmillion_spider"

    # Url stuffs
    base_url = "https://v3rmillion.net/"

    # Css stuffs
    login_form_css = "form[action=\"member.php\"]"

    # Xpath stuffs
    forum_xpath = "//td[@class=\"trow1\" or @class=\"trow2\"]/strong/" \
                  "a[contains(@href, \"forumdisplay.php?fid=\")]/@href|" \
                  "//span[@class=\"sub_control\"]/" \
                  "a[contains(@href, \"forumdisplay.php?fid=\")]/@href"
    pagination_xpath = "//div[@class=\"pagination\"]/a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_url_xpath = "//td[contains(@class,\"forumdisplay\")]/div/span/span[@class=\"smalltext\"]/a[last()]/@href|" \
                       "//span[contains(@id,\"tid\")]/a/@href"
    thread_lastmod_xpath = "//td[contains(@class,\"forumdisplay\")]/span[@class=\"lastpost smalltext\"]/text()[1]"

    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date\"]/text()[1]"

    # Regex stuffs
    topic_pattern = re.compile(
        r"tid=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%m-%d-%Y, %I:%M %p"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if "minute" in thread_date.lower():
            return datetime.today()
        elif "hour" in thread_date.lower():
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

        if "minute" in post_date.lower():
            return datetime.today()
        elif "hour" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response=response,
            formcss=self.login_form_css,
            formdata={
                "username": USER,
                "password": PASS,
                "code": "",
                "_challenge": ""
            },
            dont_filter=True,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_start
        )

    def parse_start(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        for forum_url in all_forums:
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Synchronize header user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatar content
        avatars = response.xpath('//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
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
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )

    def parse_avatar(self, response):
        file_name = response.meta.get("file_name")
        file_name_only = file_name.rsplit("/", 1)[-1]
        with open(file_name, "wb") as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar {file_name_only} done..!"
            )


class V3RMillionScrapper(SiteMapScrapper):

    spider_class = V3RMillionSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return settings


if __name__ == "__main__":
    pass

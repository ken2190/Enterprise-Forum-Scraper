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


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
USER = "hackwithme123"
PASS = "6VUZmjFzM2WtyjV"


class V3RMillionSpider(SitemapSpider):
    name = "v3rmillion_spider"

    # Url stuffs
    base_url = "https://v3rmillion.net/"

    # Css stuffs
    login_form_css = "form[action=\"member.php\"]"

    # Xpath stuffs

    # Forum xpath #
    forum_xpath = "//td[@class=\"trow1\" or @class=\"trow2\"]/strong/" \
                  "a[contains(@href, \"forumdisplay.php?fid=\")]/@href|" \
                  "//span[@class=\"sub_control\"]/" \
                  "a[contains(@href, \"forumdisplay.php?fid=\")]/@href"
    pagination_xpath = "//div[@class=\"pagination\"]/a[@class=\"pagination_next\"]/@href"

    # Thread xpath #
    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//td[contains(@class,\"forumdisplay\")]/" \
                             "div/span/span[@class=\"smalltext\"]/a[last()]/@href"
    thread_date_xpath = "//td[contains(@class,\"forumdisplay\")]/span[@class=\"lastpost smalltext\"]/text()[1]"
    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date\"]/text()[1]"

    # Avatar xpath #
    avatar_xpath = "//div[@class=\"author_avatar\"]/a/img/@src"

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
    use_proxy = True
    download_delay = REQUEST_DELAY
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

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatar content
        yield from super().parse_avatars(response)


class V3RMillionScrapper(SiteMapScrapper):

    spider_class = V3RMillionSpider
    site_name = 'v3rmillion.net'

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

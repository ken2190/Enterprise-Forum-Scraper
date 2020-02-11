import re

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

REQUEST_DELAY = 0.1
NO_OF_THREADS = 16
USERNAME = "night_cyrax"
PASSWORD = "DPO$s)sC3xzO"


class HackForumsSpider(SitemapSpider):
    name = "hackforums_spider"

    # Url stuffs
    base_url = "https://hackforums.net/"
    login_url = "https://hackforums.net/member.php?action=login"

    # Css stuffs
    login_form_css = "form[action=\"member.php\"]"

    # Xpath stuffs
    forum_xpath = "//a[contains(@href,\"forumdisplay.php\")]/@href"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span[@class=\"smalltext\" and contains(text(),\"Pages:\")]/a[last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]|" \
                        "//span[@class=\"lastpost smalltext\"]/span[@title]/@title"
    post_date_xpath = "//span[@class=\"post_date\"]/text()[contains(.,\"-\")]|" \
                      "//span[@class=\"post_date\"]/span/@title"
    avatar_xpath = "//div[@class=\"author_avatar\"]/a/img/@src"

    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"

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
    sitemap_datetime_format = "%m-%d-%Y, %I:%M %p"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"
    handle_httpstatus_list = [403, 503]
    use_proxy = False

    def parse(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        yield Request(
            url=self.login_url,
            headers=self.headers,
            callback=self.parse_login,
            meta=self.synchronize_meta(response)
        )

    def parse_login(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_form_css,
            formdata={
                "username": USERNAME,
                "password": PASSWORD,
                "quick_gauth_code": "",
                "remember": "yes",
                "submit": "Login",
                "action": "do_login",
                "url": self.base_url
            },
            dont_filter=True,
            headers=self.headers,
            meta=self.synchronize_meta(response),
            callback=self.parse_start
        )

    def parse_start(self, response):

        # Synchronize user agent for cloudfare middlewares
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

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


class HackForumsScrapper(SiteMapScrapper):

    spider_class = HackForumsSpider

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


if __name__ == "__main__":
    pass

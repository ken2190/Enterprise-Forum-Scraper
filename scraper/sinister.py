import re

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USERNAME = "seraleone"
PASSWORD = "BcCeQGx5"


class SinisterSpider(SitemapSpider):

    name = "sinister"

    # Url stuffs
    base_url = "https://sinister.ly/"
    login_url = ""

    # Css stuffs
    forum_xpath = '//td/strong/a[starts-with(@href, "Forum-")]/@href'
    login_form_css = 'form[action]'

    # Xpath stuffs
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid")]/a/@href'
    thread_last_page_xpath = './/span/span[@class="smalltext"]/a[contains(@href, "Thread-")][last()]/@href'
    thread_date_xpath = './/span[@class="lastpost smalltext"]/span[@title]/@title|' \
                        './/span[@class="lastpost smalltext"]/text()[contains(., "-")]'
    pagination_xpath = '//a[@class="pagination_next"]/@href'
    thread_pagination_xpath = '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date postbit_date"]/text()[contains(., "-")]|' \
                      '//span[@class="post_date postbit_date"]/span[@title]/@title'
    avatar_xpath = '//div[@class="author_avatar postbit_avatar"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "error")]'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r"avatar_(\d+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%m-%d-%Y"
    use_proxy = "VIP"

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_main
        )

    def parse_main(self, response):
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
        )

    def parse_forum(self, response, thread_meta={}, is_first_page=True):

        # Load sub forums
        if is_first_page:
            yield from self.parse(response)

        # Parse main forum
        yield from super().parse_forum(
            response,
            thread_meta=thread_meta,
            is_first_page=is_first_page
        )

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
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'RETRY_HTTP_CODES': [403, 406, 429, 500, 503]
            }
        )
        return settings

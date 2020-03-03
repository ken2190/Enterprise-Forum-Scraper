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


class ProcrdSpider(SitemapSpider):

    name = "procrd"

    # Url stuffs
    base_url = "https://procrd.top/"

    # Xpath stuffs
    forum_xpath = "//div[@class=\"nodeText\"]/h3[@class=\"nodeTitle\"]/a/@href"
    pagination_xpath = "//a[@class=\"PageNavNext \"]/following-sibling::a[@class=\"text\"]"

    thread_xpath = "//li[contains(@id,\"thread\")]"
    thread_first_page_xpath = "//h3[@class=\"title\"]/a/@href"
    thread_last_page_xpath = "//font/span[@class=\"itemPageNav\"][last()]/a/@href"
    thread_date_xpath = "//a[@class=\"dateTime\"]/abbr/@title|" \
                        "//a[@class=\"dateTime\"]/span[@class=\"DateTime\"]/@title"

    thread_page_xpath = "//a[contains(@class,\"currentPage\")]/text()"
    thread_pagination_xpath = "//a[contains(@class,\"currentPage\")]/preceding-sibling::a[1]/@href"

    post_date_xpath = "//div[@class=\"privateControls\"]/span[@class=\"item muted\"]/" \
                      "a/*[@class=\"DateTime\"]/@title"
    avatar_xpath = "//div[@class=\"avatarHolder\"]/a/img/@src"

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = "%d %b %Y at %H:%M"
    post_datetime_format = "%d %b %Y at %H:%M"
    month_mapper = {
        "янв": "jan",
        "фев": "feb",
        "мар": "mar",
        "апр": "apr",
        "май": "may",
        "июн": "jun",
        "июл": "jul",
        "авг": "aug",
        "сен": "sep",
        "окт": "oct",
        "ноя": "nov",
        "Дек": "dec",
        "в": "at"
    }

    def convert_russian_locale(self, text):
        # Lower case
        text = text.lower()

        # Replace month and conjunction
        for key, value in self.month_mapper.items():
            text = text.replace(key.lower(), value.lower())

        return text

    def parse_post_date(self, post_date):
        return super().parse_post_date(
            self.convert_russian_locale(post_date)
        )

    def parse_thread_date(self, thread_date):
        return super().parse_thread_date(
            self.convert_russian_locale(thread_date)
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:
            # Standardize forum url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_forum(self, response):

        # Parse sub forums
        yield from self.parse(response)

        # Parse generic forum
        yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class ProcrdScrapper(SiteMapScrapper):
    spider_class = ProcrdSpider


if __name__ == "__main__":
    pass

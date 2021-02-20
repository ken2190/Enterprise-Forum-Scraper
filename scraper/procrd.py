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

class ProcrdSpider(SitemapSpider):

    name = "procrd"

    # Url stuffs
    base_url = "https://procrd.li/"

    # Xpath stuffs
    forum_xpath = '//a[re:test(@href, "/forums/[a-zA-Z0-9-]+\.\d+/?$")]/@href'
    pagination_xpath = '//a[contains(@class, "pageNav-jump--next")]/@href'

    thread_xpath = '//div[re:test(@class, ".* ?structItem--thread ?")]'
    thread_first_page_xpath = ('.//div[@class="structItem-title"]'
                               '/a[contains(@href, "/threads/")]/@href')
    thread_last_page_xpath = '(.//span[@class="structItem-pageJump"]/a)[last()]/@href'
    thread_date_xpath = './/div[contains(@class, "structItem-cell--latest")]/a/time/@datetime'

    thread_page_xpath = '//li[contains(@class,"pageNav-page--current")]/a/text()'
    thread_pagination_xpath = ('//li[contains(@class,"pageNav-page--current")]'
                               '/preceding-sibling::li[1]/a/@href')

    post_date_xpath = '//div[contains(@class, "message-attribution-main")]/a/time/@datetime'
    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'
    use_proxy = 'On'
    
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
    post_datetime_format = "%Y-%m-%dT%H:%M:%S%z"

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class ProcrdScrapper(SiteMapScrapper):
    spider_class = ProcrdSpider
    site_type = 'forum'

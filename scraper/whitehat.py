import re
import uuid

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class WhitehatSpider(SitemapSpider):
    name = 'whitehat_spider'

    # Url stuffs
    base_url = "https://whitehat.vn/"

    # Xpath stuffs
    forum_xpath = '//div[@class="nodeText"]'\
                  '/h3[@class="nodeTitle"]/a/@href|'\
                  '//ol[@class="subForumList"]'\
                  '//a[contains(@href, "forums/")]/@href'

    pagination_xpath = '//a[@class="text" and text()="Tiếp >"]/@href'

    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = './/h3[@class="title"]/a/@href'
    thread_last_page_xpath = './/span[@class="itemPageNav"]/a[last()]/@href'
    thread_date_xpath = './/dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/@data-time|'\
                        './/dl[@class="lastPostInfo"]' \
                        '//span[@class="DateTime"]/text()|' \
                        './/dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/@data-datestring'
    thread_page_xpath = '//nav/a[contains(@class,"currentPage")]/text()'
    thread_pagination_xpath = '//nav/a[contains(text(),"< Trước")]/@href'

    post_date_xpath = '//p[@id="pageDescription"]'\
                      '//abbr[@class="DateTime"]/@data-time|'\
                      '//p[@id="pageDescription"]'\
                      '//span[@class="DateTime"]/text()'

    avatar_xpath = '//a[@data-avatarhtml="true"]/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/.*\.(\d+)/",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%d/%m/%y, %I:%M %p'
    post_datetime_format = '%d/%m/%y, %I:%M %p'

    def parse(self, response):

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'tools.25' not in forum_url:
            #     continue
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


class WhitehatScrapper(SiteMapScrapper):

    spider_class = WhitehatSpider
    site_name = 'whitehat.vn'
    site_type = 'forum'

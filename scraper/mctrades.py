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


class MctradesSpider(SitemapSpider):
    name = 'mctrades_spider'

    # Url stuffs
    base_url = "https://mctrades.org/"

    # Xpath stuffs
    forum_xpath = '//div[@class="nodeText"]'\
                  '//h3[@class="nodeTitle"]/a/@href|'\
                  '//ol[@class="subForumList"]'\
                  '//a[contains(@href, "forums/")]/@href'

    pagination_xpath = '//a[@class="text" and text()="Next >"]/@href'

    thread_xpath = '//ol[@class="discussionListItems"]/li'
    thread_first_page_xpath = './/h3[@class="title"]/a[contains(@href, "threads")]/@href'
    thread_last_page_xpath = './/span[@class="itemPageNav"]/a[last()]/@href'
    thread_date_xpath = './/dl[@class="lastPostInfo"]//span[@class="DateTime"]'\
                        '/@title|.//dl[@class="lastPostInfo"]'\
                        '//abbr[@class="DateTime"]/@data-datestring'
    thread_page_xpath = '//nav/a[contains(@class,"currentPage")]/text()'
    thread_pagination_xpath = '//nav/a[contains(text(),"< Prev")]/@href'

    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//a[@data-avatarhtml="true"]/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%d/%m/%y, %I:%M %p'
    post_datetime_format = '%d/%m/%y, %I:%M %p'

    def start_requests(self):
        # Temporary action to start spider
        yield Request(
            url=self.temp_url,
            headers=self.headers,
            callback=self.pass_cloudflare
        )

    def pass_cloudflare(self, response):
        # Load cookies and ip
        cookies, ip = self.get_cloudflare_cookies(
            base_url=self.base_url,
            proxy=True,
            fraud_check=True
        )

        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex,
                "ip": ip
            },
            cookies=cookies,
            callback=self.parse
        )

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

    def parse_forum(self, response, is_first_page=True):

        # Parse sub forums
        yield from self.parse(response)

        # Parse generic forum
        yield from super().parse_forum(response)
        
    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class MctradesScrapper(SiteMapScrapper):

    spider_class = MctradesSpider
    site_name = 'mctrades.org'
    site_type = 'forum'

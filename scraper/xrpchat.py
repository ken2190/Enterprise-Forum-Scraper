import re

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class XrpChatSpider(SitemapSpider):

    name = 'xrpchat_spider'

    # Url stuffs
    base_url = "https://www.xrpchat.com/"
    start_urls = ["https://www.xrpchat.com/"]
    # sitemap_url = "https://www.xrpchat.com/sitemap.php"

    # Regex stuffs
    topic_pattern = re.compile(
        r'topic/(\d+)-',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'(\w+.\w+)$',
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r'.*/page/(\d+)/',
        re.IGNORECASE
    )

    # Xpath stuffs
    forum_sitemap_xpath = "//sitemap[loc[contains(text(),\"content"\
                          "_forums\")]]/loc/text()"
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/topic/\")]"\
                           " and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"

    forum_xpath = '//div[@class="ipsDataItem_main"]//h4'\
                  '/a[contains(@href, "forum/")]/@href|'\
                  '//div[@class="ipsDataItem_main"]/ul/li'\
                  '/a[contains(@href, "forum/")]/@href'

    thread_xpath = '//ol[contains(@class,"cForum")]/li'
    thread_first_page_xpath = './/h4//a/@href'
    thread_last_page_xpath = './/span[contains(@class,"Pagination_last")]//a/@href'
    thread_date_xpath = './/ul//time[1]/@datetime'

    avatar_xpath = '//li[@class="cAuthorPane_photo"]/a/img/@src'

    pagination_xpath = '//li[@class="ipsPagination_next"]/a/@href'
    thread_pagination_xpath = '//li[contains(@class,"ipsPagination_prev")]/a/@href'
    thread_page_xpath = '//li[contains(@class,"Pagination_active")]//a/text()'
    post_date_xpath = '//div[contains(@class,"ipsType_reset")]//time/@title'

    def parse_thread(self, response):
        yield from super().parse_thread(response)
        yield from super().parse_avatars(response)


class XrpChatScrapper(SiteMapScrapper):

    request_delay = 0.1
    no_of_threads = 16
    spider_class = XrpChatSpider
    site_name = 'xrpchat.com'
    site_type = 'forum'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
                'RETRY_HTTP_CODES': [403, 406, 429, 500, 503]
            }
        )
        return spider_settings

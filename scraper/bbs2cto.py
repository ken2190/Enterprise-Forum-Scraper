import os
import re
from scrapy.http import Request
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class Bbs2ctoSpider(SitemapSpider):
    name = 'bbs2cto_spider'
    base_url = "http://bbs.2cto.com/"

    # Xpaths
    forum_xpath = '//a[contains(@href, "thread.php?fid=")]/@href'
    pagination_xpath = '//div[@class="pages"]'\
                       '/a[@class="pages_next"]/@href'
    thread_xpath = '//tbody[@id="threadlist"]/tr[@class="tr3"]'
    thread_first_page_xpath = '//a[contains(@class,"subject_t")]/@href'
    thread_last_page_xpath = '//span[@class="tpage"]/a[last()]/@href'
    thread_date_xpath = '//td[@class="author"]/p/a/@title'
    thread_pagination_xpath = '//div[@class="pages"]/b'\
                              '/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//div[@class="pages"]/b/text()'
    post_date_xpath = '//div[@class="tipTop s6"]/span/@title'

    avatar_xpath = '//div[@class="floot_leftdiv"]/a[img/@style]'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )
    avatar_xpath_pattern = re.compile(
        r'url\((.*?)\)',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'uid=(\d+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%Y-%m-%d %H:%M'
    post_datetime_format = '%Y-%m-%d %H:%M:%S'

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
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

        # Parse generic avatar
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        for avatar in response.xpath(self.avatar_xpath):
            avatar_url = avatar.xpath('img/@style').extract_first()

            # Standardize avatar url

            match = self.avatar_xpath_pattern.findall(avatar_url)
            if not match:
                continue
            avatar_url = match[0]
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            user_url = avatar.xpath('@href').extract_first()
            match = self.avatar_name_pattern.findall(user_url)
            if not match:
                continue

            file_name = os.path.join(
                self.avatar_path,
                f'{match[0]}.jpg'
            )

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


class Bbs2ctoScrapper(SiteMapScrapper):

    spider_class = Bbs2ctoSpider
    site_name = 'bbs.2cto.com'

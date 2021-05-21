import os
import re
from datetime import datetime

import dateparser
from scrapy import (
    Request
)

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class StormFrontSpider(SitemapSpider):
    name = "stormfront"

    # Url stuffs
    base_url = "https://www.stormfront.org/forum"

    # Xpath stuffs
    forum_xpath = '//td[starts-with(@id,"f")]//a[contains(@href, "/forum/f")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div' \
                              '/a[contains(@href, "/forum/t")]/@href'
    thread_last_page_xpath = './/td[contains(@id, "td_threadtitle_")]/div' \
                             '/span/a[contains(@href, "/forum/t")]' \
                             '[last()]/@href'
    thread_date_xpath = './/span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]' \
                      '/a[contains(@name,"post")]' \
                      '/following-sibling::text()[1]'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "VIP"
    use_cloudflare_v2_bypass = True
    cloudfare_delay = 10
    handle_httpstatus_list = [503]
    post_datetime_format = '%m-%d-%Y, %I:%M %p'
    thread_datetime_format = '%m-%d-%Y'
    sitemap_datetime_format = '%m-%d-%Y'

    def parse_thread_date(self, thread_date):
        if not thread_date:
            return
        try:
            return datetime.strptime(
                thread_date.strip(),
                self.thread_datetime_format
            )
        except:
            return dateparser.parse(thread_date).replace(tzinfo=None)

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        # print(response.text)
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
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

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        for avatar in response.xpath(self.avatar_xpath):
            avatar_url = avatar.xpath('img/@src').extract_first()

            # Standardize avatar url
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


class StormFrontScrapper(SiteMapScrapper):
    spider_class = StormFrontSpider
    site_name = 'stormfront.org'
    site_type = 'forum'

import re
from datetime import datetime
from urllib.parse import urlencode

from scrapy.http import Request

from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


class DarkTimeSpider(SitemapSpider):
    name = 'darktime_spider'
    base_url = 'https://dark-time.com'

    # Xpaths
    forum_xpath = '//h3[@class="node-title"]/a/@href|' \
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]' \
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]' \
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]' \
                        '/@data-time'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]' \
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]' \
                        '/a/text()'
    post_date_xpath = '//article[contains(@class,"message--post")]' \
                      '//time[@data-time]/@data-time'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"/threads/(\d+)",
        re.IGNORECASE
    )

    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    use_cloudflare_v2_bypass = True
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def extract_csrf_token(self, response):
        csrf_token = response.xpath('//html[@data-csrf]/@data-csrf').extract_first()
        return csrf_token

    def start_requests(self, cookiejar=None, ip=None):
        """
        :return: => request start urls if no sitemap url or no start date
                 => request sitemap url if sitemap url and start date
        """

        # Load meta
        meta = {}
        if cookiejar:
            meta["cookiejar"] = cookiejar
        if ip:
            meta["ip"] = ip

        # Branch choices requests
        yield Request(
            url=self.base_url,
            headers=self.headers,
            errback=self.check_site_error,
            callback=self.change_language_to_english,
            dont_filter=True,
            meta=meta
        )

    def change_language_to_english(self, response):
        self.synchronize_headers(response)
        csrf_token = self.extract_csrf_token(response)
        params = (
            ('language_id', '1'),
            ('_xfRedirect', self.base_url),
            ('t', csrf_token),
        )
        change_language_url = self.base_url + '/?' + urlencode(params)
        yield response.follow(
            url=change_language_url,
            meta=self.synchronize_meta(response),
            callback=self.parse
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        try:
            return datetime.fromtimestamp(float(thread_date))
        except:
            return datetime.strptime(
                thread_date.strip(),
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        try:
            return datetime.fromtimestamp(float(post_date))
        except:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )

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
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class DarkTimeScrapper(SiteMapScrapper):
    spider_class = DarkTimeSpider
    site_name = 'dark-time.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [403, 406, 429, 500, 503],
            }
        )
        return settings

import re
import dateparser

from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


class ArmadaboardSpider(SitemapSpider):
    name = 'armadaboard_spider'
    base_url = 'https://www.armadaboard.com/'

    # Xpaths
    forum_xpath = '//a[@class="forumlink"]/@href'
    thread_xpath = '//tr[td/span/a[@class="gen"]]'
    thread_first_page_xpath = './/span[@class="genmed" or @class="gen"]/a/@href'
    thread_last_page_xpath = './/span[@class="gensmall"]/a[last()]/@href'
    thread_date_xpath = './/span[@class="postdetails" and a]/text()[1]'
    pagination_xpath = '//span[@class="gensmall"]//a[text()="След."]/@href'
    thread_pagination_xpath = '//span[@class="gensmall12"]/a[text()="След."]/@href'
    thread_page_xpath = '//span[@class="gensmall12"]/b/text()'
    post_date_xpath = '//td[@class="desktop768"]//span[@class="postdetails"]//text()'

    avatar_xpath = '//td[contains(@class, "avatar")]//table[2]//td//img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    post_datetime_format = '%a %d %b, %Y %H:%M'
    sitemap_datetime_format = '%a %d %b, %Y %H:%M'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        thread_date = ' '.join(thread_date.strip().split(' ')[1:])

        try:
            return datetime.strptime(
                thread_date.strip(),
                self.post_datetime_format
            ) - timedelta(hours=3)
        except:
            return dateparser.parse(thread_date).replace(tzinfo=None) - timedelta(hours=3)


    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        post_date = post_date.replace('Добавлено:', '').strip()
        post_date = ' '.join(post_date.split(' ')[1:])

        try:
            return datetime.strptime(
                post_date.strip(),
                self.post_datetime_format
            )
        except:
            return dateparser.parse(post_date).replace(tzinfo=None)

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class ArmadaboardScrapper(SiteMapScrapper):
    spider_class = ArmadaboardSpider
    site_name = 'armadaboard.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings

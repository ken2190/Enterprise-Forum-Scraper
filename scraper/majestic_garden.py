import os
import re
import scrapy
from math import ceil
import configparser
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


USER = 'cyrax11'
PASS = 'Night#Majestic'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'

PROXY = 'http://127.0.0.1:8118'


class MajesticGardenSpider(SitemapSpider):
    name = 'majestic_garden_spider'
    base_url = 'http://garden2b7zwrjskh2y3f4pkscgg2waogjp2ilax2mvikjlzmamylznad.onion'
    index_url = 'http://garden2b7zwrjskh2y3f4pkscgg2waogjp2ilax2mvikjlzmamylznad.onion/index.php'

    # Xpaths
    forum_xpath = '//a[contains(@href, "index.php?board=")]/@href'
    pagination_xpath = '//div[@class="pagelinks floatleft"]'\
                       '/strong/following-sibling::a[1]/@href'
    thread_xpath = '//div[@id="messageindex"]//tr[td[contains(@class,"subject")]]'
    thread_first_page_xpath = './/span[contains(@id,"msg_")]/a/@href'
    thread_last_page_xpath = './/small[contains(@id,"pages")]/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class, "lastpost")]/br'\
                        '/preceding-sibling::text()[1]'
    thread_pagination_xpath = '//div[@class="pagelinks floatleft"]'\
                              '/strong/preceding-sibling::a[1]/@href'
    thread_page_xpath = '//div[@class="pagelinks floatleft"]'\
                        '/strong/text()'
    post_date_xpath = '//div[@class="keyinfo"]'\
                      '/div[@class="smalltext"]/text()[last()]'

    avatar_xpath = '//li[@class="avatar"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//p[@class="error"]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*p=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"attach=(\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    sitemap_datetime_format = "%B %d, %Y, %I:%M:%S %p"
    post_datetime_format = "%B %d, %Y, %I:%M:%S %p »"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "user-agent": USER_AGENT
        })

    def start_requests(self):
        yield Request(
            url=self.index_url,
            callback=self.proceed_for_login,
            headers=self.headers,
            meta={
                'proxy': PROXY
            },
            dont_filter=True
        )

    def proceed_for_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        token = response.xpath(
            '//p[@class="centertext smalltext"]/'
            'following-sibling::input[1]'
        )
        if not token:
            return
        token_key = token[0].xpath('@name').extract_first()
        token_value = token[0].xpath('@value').extract_first()
        form_data = {
            "cookieneverexp": "on",
            "hash_passwrd": "",
            "passwrd": PASS,
            "user": USER,
            token_key: token_value,
        }
        login_url = f'{self.index_url}?action=login2'
        yield FormRequest(
            url=login_url,
            headers=self.headers,
            formdata=form_data,
            callback=self.parse_start,
            meta=self.synchronize_meta(response),
            dont_filter=True,
        )

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)
        
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if not forum_url.endswith('board=50.0'):
            #     continue
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
        yield from super().parse_avatars(response)

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        try:
            file_name = os.path.join(
                self.avatar_path,
                self.avatar_name_pattern.findall(url)[0]
            )
            return f'{file_name}.jpg'
        except Exception as err:
            return


class MajesticGardenScrapper(SiteMapScrapper):

    spider_class = MajesticGardenSpider
    site_name = 'majestic_garden'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

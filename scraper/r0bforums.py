import re
from scrapy.http import Request, FormRequest
from datetime import datetime, timedelta
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5

USER = 'vrx9'
PASS = 'Night#Vrx099'

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class R0bForumsSpider(SitemapSpider):
    name = 'r0bforums_spider'
    base_url = "https://r0bforums.com/"

    # Xpaths
    forum_xpath = '//a[contains(@href, "forumdisplay.php?fid=")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[contains(@class,"smalltext")]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()[1]'

    avatar_xpath = '//div[@class="author_avatar"]/a/img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    handle_httpstatus_list = [503]
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%m-%d-%Y'
    post_datetime_format = '%m-%d-%Y'

    def start_requests(self):
        login_url = 'https://r0bforums.com/member.php?action=login'
        yield Request(
            url=login_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.process_login,
        )

    def process_login(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        my_post_key = response.xpath(
                '//input[@name="my_post_key"]/@value').extract_first()
        formdata = {
                'username': USER,
                'password': PASS,
                'remember': 'yes',
                'submit': 'Login',
                'action': 'do_login',
                'url': self.base_url,
                'my_post_key': my_post_key,
            }
        yield FormRequest(
            url=f"{self.base_url}member.php",
            formdata=formdata,
            headers=self.headers,
            callback=self.parse,
            dont_filter=True,
            meta=self.synchronize_meta(response),
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        url = 'https://r0bforums.com/index.php'
        yield Request(
            url=url,
            callback=self.parse_start,
            headers=self.headers,
            meta=self.synchronize_meta(response),
        )

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.split(',')[0].strip()
        if not thread_date:
            return

        if 'hour' in thread_date.lower():
            return datetime.today()
        elif 'yesterday' in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return

        if 'hour' in post_date.lower():
            return datetime.today()
        elif 'yesterday' in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse_start(self, response):
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
        yield from super().parse_avatars(response)


class R0bForumsScrapper(SiteMapScrapper):

    spider_class = R0bForumsSpider
    site_name = 'r0bforums.com'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

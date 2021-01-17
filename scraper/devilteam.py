
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


<<<<<<< HEAD
REQUEST_DELAY = 1
NO_OF_THREADS = 1

USERNAME = "Cyrax_0111"
=======
USERNAME = "Cyrax_011"
>>>>>>> df60255be9b7aafbba28c8972c29ac0bcc8bc0ae
PASSWORD = "Night#India065"
MAX_TRY_TO_LOG_IN_COUNT = 3


class DevilTeamSpider(SitemapSpider):
    name = 'devilteam_spider'
    base_url = "https://devilteam.pl"

    # xpaths
    login_form_xpath = '//form[@id="login"]'
    forum_xpath = '//a[contains(@class, "forumtitle")]/@href'

    pagination_xpath = '//li[@class="arrow next"]/a/@href'

    thread_xpath = '//ul[@class="topiclist topics"]/li'
    thread_first_page_xpath = './/a[contains(@class, "topictitle")]/@href'
    thread_last_page_xpath = './/div[@class="pagination"]'\
                             '/ul/li[last()]/a/@href'
    thread_date_xpath = './/dd[@class="lastpost"]/span/time/@datetime'
    thread_page_xpath = '//li[contains(@class, "ipsPagination_active")]'\
                        '/a/text()'
    thread_pagination_xpath = '//li[@class="arrow previous"]'\
                              '/a[@rel="prev"]/@href'

    post_date_xpath = '//p[@class="author"]//time/@datetime'

    avatar_xpath = '//span[@class="avatar"]/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "error")]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"&t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True

    def start_requests(self):
        self._try_to_log_in_count = 0

        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_start,
            meta={
                "cookiejar": uuid.uuid1().hex,
                "ip": self.ip_handler.get_good_ip()
            }
        )

    def parse_start(self, response):
        self._try_to_log_in_count += 1

        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        login_form = response.xpath(self.login_form_xpath)

        def get_field_value(name):
            return login_form.xpath(f'.//input[@name="{name}"]/@value').getall()[-1]

        formdata = {
            'username': USERNAME,
            'password': PASSWORD,
            'redirect': get_field_value('redirect'),
            'creation_time': get_field_value('creation_time'),
            'form_token': get_field_value('form_token'),
            'sid': get_field_value('sid'),
            'login': get_field_value('login')
        }

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            dont_click=True,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class DevilTeamScrapper(SiteMapScrapper):

    spider_class = DevilTeamSpider
    site_name = 'devilteam.pl'
    site_type = 'forum'

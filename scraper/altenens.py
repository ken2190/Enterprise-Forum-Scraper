import re
import json
from lxml.html import fromstring
from urllib.parse import urlencode

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scrapy.exceptions import CloseSpider
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USER = 'thecreator'
PASS = 'Night#Altens001'


class AltenensSpider(SitemapSpider):
    name = 'altenens_spider'

    # Url stuffs
    base_url = "https://altenen.is/"

    # Xpaths
    login_form_xpath = '//form[@method="post"]'
    # captcha_form_xpath = '//form[@id="recaptcha-form"]'
    forum_xpath = '//h3[@class="node-title"]/a/@href|'\
                  '//a[contains(@class,"subNodeLink--forum")]/@href'
    thread_xpath = '//div[contains(@class, "structItem structItem--thread")]'
    thread_first_page_xpath = './/div[@class="structItem-title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="structItem-pageJump"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/time[contains(@class, "structItem-latestDate")]'\
                        '/@datetime'
    pagination_xpath = '//a[contains(@class,"pageNav-jump--next")]/@href'
    thread_pagination_xpath = '//a[contains(@class, "pageNav-jump--prev")]'\
                              '/@href'
    thread_page_xpath = '//li[contains(@class, "pageNav-page--current")]'\
                        '/a/text()'
    post_date_xpath = '//div/a/time[@datetime]/@datetime'

    avatar_xpath = '//div[@class="message-avatar-wrapper"]/a/img/@src'

    # Login Failed Message
    login_failed_xpath = '//div[contains(@class, "blockMessage blockMessage--error")]'
    
    # Other settings
    use_proxy = True
    handle_httpstatus_list = [403]
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    topic_pattern = re.compile(
        r'threads/.*\.(\d+)/',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_main
        )

    def parse_main(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load token
        match = re.findall(r'csrf: \'(.*?)\'', response.text)

        # Load param
        params = {
            '_xfRequestUri': '/',
            '_xfWithData': '1',
            '_xfToken': match[0],
            '_xfResponseType': 'json'
        }
        token_url = 'https://altenen.is/login/?' + urlencode(params)
        yield Request(
            url=token_url,
            headers=self.headers,
            callback=self.proceed_for_login,
            meta=self.synchronize_meta(response)
        )

    def proceed_for_login(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load json data
        json_response = json.loads(response.text)
        html_response = fromstring(json_response['html']['content'])

        # Exact token
        token = html_response.xpath(
            '//input[@name="_xfToken"]/@value')[0]
        params = {
            'login': USER,
            'password': PASS,
            "remember": '1',
            '_xfRedirect': '',
            '_xfToken': token
        }
        yield FormRequest(
            url="https://altenen.is/login/login",
            callback=self.parse,
            formdata=params,
            headers=self.headers,
            dont_filter=True,
        )

    def parse_thread(self, response):

        if response.status == 403:
            err_msg = response.css(
                '.p-body-pageContent > .blockMessage::text').get()
            if err_msg:
                self.logger.warning('%s - %s', response.url, err_msg.strip())

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class AltenensScrapper(SiteMapScrapper):

    spider_class = AltenensSpider
    site_name = 'altenen.is'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [403, 406, 408, 429, 500, 502, 503, 504, 522, 524],
            'CLOSESPIDER_ERRORCOUNT': 1
        })
        return settings

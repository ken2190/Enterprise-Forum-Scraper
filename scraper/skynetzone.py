import os
import re
import uuid
import json
import dateparser

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = "Cyrax_011"
PASSWORD = "Night#India065"

class SkyNetZoneSpider(SitemapSpider):

    name = 'skynetzone_spider'

    # Url stuffs
    base_url = 'https://skynetzone.pw'
    login_url = f'{base_url}/login/login'

    # Regex stuffs
    topic_pattern = re.compile(r'threads/(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)')

    # Xpath stuffs
    login_form_xpath = "//form[@method='post']"
    forum_xpath = "//a[contains(@href,\"/forums\")]/@href"
    pagination_xpath = "//a[contains(@class,\"pageNav-jump--next\")]/@href"
    thread_xpath = "//div[contains(@class,\"structItem--thread\")]"
    thread_first_page_xpath = "//div[@class=\"structItem-title\"]/a/@href"
    thread_last_page_xpath = "//span[@class=\"structItem-pageJump\"]/"\
                             "a[last()]/@href"
    thread_date_xpath = "//time[contains(@class,\"structItem-latestDate\")]"\
                        "/@title"
    thread_pagination_xpath = "//a[contains(@class,\"pageNav-jump--prev\")]"\
                              "/@href"
    thread_page_xpath = "//li[contains(@class,\"pageNav-page--current\")]"\
                        "/a/text()"
    post_date_xpath = "//div[@class=\"message-attribution-main\"]"\
                      "/a[@class=\"u-concealed\"]/time/@title"

    avatar_xpath = "//img[contains(@class,\"avatar\")]/@src"

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//div[@data-sitekey]/@data-sitekey'

    # Other settings
    use_proxy = True
    download_delay = 0.3
    download_thread = 10

    def parse_thread_date(self, thread_date):
        thread_date = thread_date.strip()[:-5]
        if not thread_date:
            return
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):
        post_date = post_date.strip()[:-5]
        return dateparser.parse(post_date)

    def start_requests(self):
        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login,
        )

    def parse_login(self, response):
        self.synchronize_headers(response)
        # Solve hcaptcha
        captcha_response = self.solve_recaptcha(response)
        self.logger.debug(f'captcha_response: {captcha_response}')
        token = response.xpath(
            '//input[@name="_xfToken"]/@value').extract_first()
        formdata = {
            'login': USERNAME,
            'password': PASSWORD,
            'g-recaptcha-response': captcha_response,
            "remember": '1',
            '_xfRedirect': self.base_url,
            '_xfToken': token
        }
        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata=formdata,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
        )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class SkyNetZoneScrapper(SiteMapScrapper):

    spider_class = SkyNetZoneSpider
    site_name = 'skynetzone.pw'

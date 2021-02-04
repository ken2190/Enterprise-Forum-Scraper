
import re
import uuid
from datetime import datetime

import js2py
import requests
from scrapy import Request, FormRequest

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

class YouGameSpider(SitemapSpider):
    name = 'yougame_spider'

    # Url stuffs
    base_url = "https://yougame.biz"

    # Xpaths
    captcha_form_xpath = '//form[@id="recaptcha-form"]'
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

    # Recaptcha stuffs
    recaptcha_site_key_xpath = '//button[@class="g-recaptcha"]/@data-sitekey'

    # Other settings
    use_proxy = "On"
    fraudulent_threshold = 50
    handle_httpstatus_list = [503]
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    def start_requests(self):
        meta = {
            "cookiejar": uuid.uuid1().hex,
            "ip": self.ip_handler.get_good_ip()
        }

        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse,
            errback=self.check_site_error,
            dont_filter=True,
            meta=meta
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        if "slowAES.decrypt" in response.text:
            protected2 = self.get_protected_cookies(response)
            headers = self.headers.copy()
            headers['cookie'] = protected2
            yield response.follow(
                url=self.base_url,
                callback=self.parse,
                dont_filter=True,
                meta=self.synchronize_meta(response),
                headers=headers
            )
            return

        if response.xpath(self.captcha_form_xpath):
            recaptcha_token = self.solve_recaptcha(response).solution.token

            yield FormRequest.from_response(
                response,
                formxpath=self.captcha_form_xpath,
                formdata={
                    "g-recaptcha-response": recaptcha_token
                },
                meta=self.synchronize_meta(response),
                dont_filter=True,
                headers=self.headers,
                callback=self.parse_start
            )
        else:
            yield from self.parse_start(response)

    def get_protected_cookies(self, response):
        toNumbers = re.findall(r'(function toNumbers.*)function', response.text)[0]
        toHex = re.findall(r'(function toHex.*})var', response.text)[0]
        f_n, s_n, t_n = re.findall(r'toNumbers\(\"(\w*)\"\)', response.text)
        checkjs_url = response.xpath('//script[@type]//@src').extract()[0]
        checkjs = requests.get(checkjs_url).text
        checkjs = js2py.eval_js(checkjs)
        toNumbers = js2py.eval_js(toNumbers)
        toHex = js2py.eval_js(toHex)
        f_n = toNumbers(f_n)
        s_n = toNumbers(s_n)
        t_n = toNumbers(t_n)
        tmp = checkjs.decrypt(t_n, 2, f_n, s_n)
        cookie = f"Protected2={toHex(tmp)}; expires=Thu, 31-Dec-37 23:55:55 GMT; path=/"

        return cookie

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """

        return datetime.strptime(
            thread_date.strip()[:-5],
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        return datetime.strptime(
            post_date.strip()[:-5],
            self.post_datetime_format
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            # if 'forums/746/' not in forum_url:
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


class YouGameScrapper(SiteMapScrapper):

    spider_class = YouGameSpider
    site_name = 'yougame.biz'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update({
            'RETRY_HTTP_CODES': [406, 429, 500, 503]
        })
        return settings

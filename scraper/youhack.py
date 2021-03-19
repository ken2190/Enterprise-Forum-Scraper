import os
import re
import uuid
import dateparser

from datetime import datetime
from scrapy.utils.gz import gunzip

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class YouHackSpider(SitemapSpider):

    name = 'youhack_spider'

    base_url = "https://youhack.xyz/"

    # Xpath stuffs
    captcha_form_css = "form[action]"
    forum_xpath = '//h3[@class="nodeTitle"]/a[contains(@href, "forums/")]/@href|'\
                    '//ol[@class="subForumList"]//h4[@class="nodeTitle"]/a/@href'
    thread_xpath = '//li[contains(@id, "thread-")]'
    thread_first_page_xpath = './/h3[@class="title"]'\
                              '/a[contains(@href,"threads/")]/@href'
    thread_last_page_xpath = './/span[@class="itemPageNav"]'\
                             '/a[last()]/@href'
    thread_date_xpath = './/dl[@class="lastPostInfo"]'\
                        '//a[@class="dateTime"]/*/@title'
    pagination_xpath = '//nav/a[last()]/@href'
    thread_pagination_xpath = '//nav/a[@class="text"]/@href'
    thread_page_xpath = '//nav//a[contains(@class, "currentPage")]'\
                        '/text()'
    post_date_xpath = '//div[@class="messageDetails"]'\
                      '//span[@class="DateTime"]/text()|'\
                      '//div[@class="messageDetails"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'

    avatar_xpath = '//div[@class="avatarHolder"]/a/img/@src'
    
    recaptcha_site_key_xpath = '//div[@class="g-recaptcha"]/@data-sitekey'
    # Regex stuffs
    topic_pattern = re.compile(
        r"threads/(\d+)/",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\w+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"page-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = "%d/%m/%y"
    post_datetime_format = "%d/%m/%y"

    def parse_thread_date(self, thread_date):
        if not thread_date:
            return
        return dateparser.parse(thread_date.strip())

    def parse_post_date(self, post_date):
        if not post_date:
            return
        return dateparser.parse(post_date.strip())

    def start_requests(self,):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse_captcha,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True,
        )

    def parse_captcha(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        if response.xpath(self.recaptcha_site_key_xpath):
            formdata = {
                "g-recaptcha-response": self.solve_recaptcha(response).solution.token,
                "swp_sessionKey": response.xpath("//input[@name='swp_sessionKey']/@value").extract_first()
            }

            yield FormRequest.from_response(
                response,
                formcss=self.captcha_form_css,
                formdata=formdata,
                meta=self.synchronize_meta(response),
                dont_filter=True,
                headers=self.headers,
                callback=self.parse
            )
        else:
            yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True,
        )

    def parse(self, response):
        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)
        
        if response.xpath(self.recaptcha_site_key_xpath):
            yield Request(
                url=self.base_url,
                headers=self.headers,
                callback=self.parse_captcha,
                meta={
                    "cookiejar": uuid.uuid1().hex
                },
                dont_filter=True,
            )

        # Load all forums
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
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)
        

class YouHackScrapper(SiteMapScrapper):

    spider_class = YouHackSpider
    site_name = 'youhack.ru'
    site_type = 'forum'
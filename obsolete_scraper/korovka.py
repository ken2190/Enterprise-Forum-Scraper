import os
import uuid
import re
import sys
import scrapy
import hashlib
from math import ceil
import configparser
from scrapy import (
    Request,
    FormRequest
)

from datetime import datetime, timedelta

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = .2
NO_OF_THREADS = 1

CODE = 'shithead'
USER = "nsfw3"
PASS = 'Night#NSFW00'


class KorovkaSpider(SitemapSpider):

    name = 'korovka_spider'

    # Url stuffs
    base_url = "https://korovka.cc/"
    login_url = "https://korovka.cc/login.php?do=login"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forumdisplay.php?f=")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = '//span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"]'\
                      '/a[contains(@name,"post")]/following-sibling::text()'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Other settings
    use_proxy = "On"
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y, %H:%M'

    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.firstrun = kwargs.get('firstrun')

    def start_requests(self):
        md5_pass = hashlib.md5(PASS.encode('utf-8')).hexdigest()
        formdata = {
            "vb_login_username": USER,
            "vb_login_password": "",
            "vb_login_md5password": md5_pass,
            "vb_login_md5password_utf": md5_pass,
            "cookieuser": '1',
            "url": "/",
            "do": "login"
        }

        yield FormRequest(
            self.login_url,
            formdata=formdata,
            headers=self.headers,
            callback=self.parse_redirect,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse_redirect(self, response):
        yield FormRequest.from_response(
            response,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_code
        )

    def parse_code(self, response):
        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)
        code_block = response.xpath(
            '//td[contains(text(), "буквы Вашего кодового слова форму")]'
            '/text()').re(r'Введите (\d+)-.*? и (\d+)')
        if not code_block:
            code_block = response.xpath(
                '//td[contains(text(), "Your code words in the form below")]'
                '/text()').re(r'Type (\d+)-.*? and (\d+)')
        security_token = response.xpath(
            '//input[@name="securitytoken"]/@value').extract_first()
        s = response.xpath(
            '//input[@name="s"]/@value').extract_first()
        code = ''
        for c in code_block:
            code += CODE[int(c) - 1]
        formdata = {
            'apa_authcode': code,
            's': s,
            'securitytoken': security_token
        }
        print(formdata)
        code_submit_url = f'{self.base_url}misc.php?do=apa&check=1'
        yield FormRequest(
            url=code_submit_url,
            callback=self.parse_start,
            formdata=formdata,
            headers=self.headers,
            meta=self.synchronize_meta(response)
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()

        if 'сегодня' in thread_date.lower():
            return datetime.today()
        elif "вчера" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.strip()

        if "сегодня" in post_date.lower():
            return datetime.today()
        elif "вчера" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        if self.firstrun:
            self.output_url_file = open(self.output_path + '/urls.txt', 'w')
            all_forums = response.xpath(self.forum_xpath).extract()
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
        else:
            input_file = self.output_path + '/urls.txt'
            if not os.path.exists(input_file):
                self.logger.info('URL File not found. Exiting!!')
                return
            for thread_url in open(input_file, 'r'):
                thread_url = thread_url.strip()
                topic_id = self.topic_pattern.findall(thread_url)
                if not topic_id:
                    continue
                file_name = '{}/{}-1.html'.format(
                    self.output_path, topic_id[0])
                if os.path.exists(file_name):
                    continue
                yield Request(
                    url=thread_url,
                    headers=self.headers,
                    callback=self.parse_thread,
                    meta=self.synchronize_meta(
                        response,
                        default_meta={
                            "topic_id": topic_id[0]
                        }
                    )
                )

    def parse_forum(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(self.thread_first_page_xpath).extract()
        for thread_url in threads:
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            # if 'showthread.php?t=' not in thread_url:
            #     continue
            self.output_url_file.write(thread_url)
            self.output_url_file.write('\n')

        next_page = response.xpath(self.pagination_xpath).extract_first()
        if next_page:
            if self.base_url not in next_page:
                next_page = self.base_url + next_page
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):
        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
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


class KorovkaScrapper(SiteMapScrapper):

    spider_class = KorovkaSpider
    site_name = 'korovka.cc'

import re
import os
import uuid

from datetime import datetime, timedelta

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 1
NO_OF_THREADS = 1
USERNAME = "vrx9"
PASSWORD = "4hr63yh38a"


class WeLeakDataSpider(SitemapSpider):

    name = "weleakdata"

    # Url stuffs
    base_url = "https://weleakdata.com/"

    # Xpath stuffs

    # Login form xpath
    login_form_xpath = '//form[@action="login.php?do=login"]'

    # Forum xpath #
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
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]'\
                      '/div[last()]/a[contains(@name,"post")]'\
                      '/following-sibling::text()[1]'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = True
    cloudfare_delay = 10
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%m-%d-%Y, %I:%M %p'
    sitemap_datetime_format = '%m-%d-%Y'

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()
        if "today" in thread_date.lower():
            return datetime.today()
        elif "yesterday" in thread_date.lower():
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
        if not post_date:
            return

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            },
            dont_filter=True
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "vb_login_username": USERNAME,
                "vb_login_password": PASSWORD,
            },
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_redirect
        )

    def parse_redirect(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            meta=self.synchronize_meta(response),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start,
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        base_forum_url = "https://weleakdata.com/forumdisplay.php?f={}"
        for i in range(1, 30):
            forum_url = base_forum_url.format(i)
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
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


class WeLeakDataScrapper(SiteMapScrapper):

    spider_class = WeLeakDataSpider
    site_name = 'weleakdata.com'


if __name__ == '__main__':
    pass

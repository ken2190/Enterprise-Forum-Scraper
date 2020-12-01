import os
import re
import time

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


USERNAME = "darkcylon"
PASSWORD = "Night#Omerta"
MD5PASS = "8956fb126e264fcf3da8a553e271a0c9"


class OmertaSpider(SitemapSpider):
    name = 'omerta_spider'

    # Url stuffs
    base_url = "https://omerta.cc/"

    # Css stuffs
    login_form_css = "form[action*=login]"

    # Xpath stuffs
    forum_xpath = "//tr[@align=\"center\"]//a[contains(@href, \"forumdisplay.php?f=\")]/@href"
    pagination_xpath = "//td[@class=\"pagenav_control\"]/a[@rel=\"next\"]/@href"

    thread_xpath = "//tbody[contains(@id,\"threadbits_forum\")]/tr[not(@valign)]"

    thread_first_page_xpath = ".//a[contains(@id,\"thread_title\")]/@href"
    thread_last_page_xpath = ".//td[contains(@id,\"td_threadtitle\")]/div/span[@class=\"smallfont\"]/a[last()]/@href"
    thread_date_xpath = ".//td[not(@nowrap)]/div/span[@class=\"time\"]/preceding-sibling::text()"

    thread_pagination_xpath = "//td[@class=\"pagenav_control\"]/a[@rel=\"prev\"]/@href"
    thread_page_xpath = "//span[contains(@title,\"Showing results\")]/strong/text()"
    post_date_xpath = "//a[contains(@name,\"post\")]/following-sibling::text()[contains(.,\":\")]"

    password_protect_xpath = "//div[@class=\"panel\"]/div/div/p[contains(text(),\"password protected\")]"

    # Login Failed Message
    login_failed_xpath = '//div[contains(text(), "an invalid username or password")]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    use_vip_proxy = True
    sitemap_datetime_format = "%m-%d-%Y"
    post_datetime_format = "%m-%d-%Y, %I:%M %p"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
        )

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

        if "today" in post_date.lower():
            return datetime.today()
        elif "yesterday" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def parse(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response=response,
            meta=self.synchronize_meta(response),
            formcss=self.login_form_css,
            formdata={
                "vb_login_username": USERNAME,
                "vb_login_password": PASSWORD,
                # "securitytoken": "guest",
                # "vb_login_md5password": MD5PASS,
                # "vb_login_md5password_utf": MD5PASS,
                # "do": "login",
                # "url": "/"
            },
            headers=self.headers,
            dont_filter=True,
            dont_click=True,
            callback=self.parse_login
        )

    def parse_login(self, response):
        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)
        time.sleep(2)

        # Check if login failed
        self.check_if_logged_in(response)

        yield Request(
            url=self.base_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_start,
            meta=self.synchronize_meta(response)
        )

    def parse_start(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("forum/forum_count", len(all_forums))

        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:

                if forum_url[0] == "/":
                    forum_url = forum_url[1:]

                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        # Check if password protected
        password_protected = response.xpath(self.password_protect_xpath).extract_first()
        if password_protected:
            self.logger.info(
                "Thread %s has been protected by password. Ignored." % response.url
            )
            return

        # Parse generic thread
        yield from super().parse_thread(response)

        # Save avatars
        avatars = response.xpath("//a[contains(@href,\"member.php?\")]/img")
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            user_id = avatar.xpath('@alt').re(r'(\w+)\'s')
            if not user_id:
                continue
            file_name = '{}/{}.jpg'.format(self.avatar_path, user_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name,
                        "user_id": user_id[0]
                    }
                )
            )

    def parse_avatar(self, response):
        file_name = response.meta.get("file_name")
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(
                f"Avatar for user {response.meta['user_id']} done..!"
            )


class OmertaScrapper(SiteMapScrapper):

    request_delay = 0.3
    no_of_threads = 12
    spider_class = OmertaSpider
    site_name = 'omerta.cc'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
            }
        )
        return settings


if __name__ == "__main__":
    pass

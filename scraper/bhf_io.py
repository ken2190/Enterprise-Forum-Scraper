import os
import re
from datetime import datetime

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = "thecreator101@protonmail.com"
PASSWORD = "Night#Bhf01"


class BHFIOSpider(SitemapSpider):

    name = 'bhfio_spider'

    # Url stuffs
    base_url = 'https://bhf.io'
    login_url = 'https://bhf.io/login/login'
    start_urls = ["https://bhf.io/"]
    sitemap_url = "https://bhf.io/sitemap.php"

    # Regex stuffs
    topic_pattern = re.compile(r'threads/(\d+)')
    avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
    pagination_pattern = re.compile(r'.*page-(\d+)')

    # Css stuffs
    login_form_css = "form[action]"
    backup_code_css = "a[href*=\"provider=backup\"]::attr(href)"
    account_css = r'a[href="/account/"]'

    # Xpath stuffs
    forum_sitemap_xpath = "//sitemap/loc/text()"
    thread_sitemap_xpath = "//url[loc[contains(text(),\"/threads/\")] and lastmod]"
    thread_url_xpath = "//loc/text()"
    thread_lastmod_xpath = "//lastmod/text()"

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    download_delay = 0.3
    download_thread = 10

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "middlewares.middlewares.BypassCloudfareMiddleware": 200
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
        },
        'DOWNLOAD_DELAY': download_delay,
        'CONCURRENT_REQUESTS': download_thread,
        'CONCURRENT_REQUESTS_PER_DOMAIN': download_thread
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Update headers
        self.headers.update(
            {
                'referer': 'https://bhf.io/',
            }
        )

        # Load backup codes
        self.backup_code_file = os.path.join(
            #os.getcwd(),
            "/opt/forumparser/code/%s" % self.name
        )
        with open(
            file=self.backup_code_file,
            mode="r",
            encoding="utf-8"
        ) as file:
            self.backup_codes = [
                code.strip() for code in file.read().split("\n")
            ]

    def write_backup_codes(self):
        with open(
            file=self.backup_code_file,
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(
                "\n".join(self.backup_codes)
            )

    def start_requests(self):
        yield Request(
            url=self.login_url,
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_login
        )

    def parse_login(self, response):
        yield FormRequest.from_response(
            response=response,
            formcss=self.login_form_css,
            formdata={
                "login": USERNAME,
                "password": PASSWORD
            },
            dont_filter=True,
            callback=self.parse_post_login
        )

    def parse_post_login(self, response):
        backup_code_url = "%s%s" % (
            self.base_url,
            response.css(self.backup_code_css).extract_first()
        )
        yield Request(
            url=backup_code_url,
            headers=self.headers,
            dont_filter=True,
            callback=self.parse_backup_code
        )

    def parse_backup_code(self, response):

        # Load backup code
        code = self.backup_codes[0]
        self.backup_codes = self.backup_codes[1:]

        yield FormRequest.from_response(
            response=response,
            formcss=self.login_form_css,
            formdata={
                "code": code.replace(" ", ""),
                "trust": "0",
                "remember": "0"
            },
            meta={
                "backup_code_url": response.request.url,
                "code": code
            },
            dont_filter=True,
            callback=self.parse_post_backup_code
        )

    def parse_post_backup_code(self, response):

        # Load backup code
        backup_code_url = response.meta.get("backup_code_url")

        # Load code
        code = response.meta.get("code")

        # Load account
        account = response.css(self.account_css).extract_first()

        # If not account and no more backup codes, return
        if not account and not self.backup_codes:
            self.logger.info(
                "None of backup code work."
            )
            self.write_backup_codes()
            return

        # If not account, try other code
        if not account:
            self.logger.info(
                "Code %s failed." % code
            )

            with open(
                file="%s.html" % code,
                mode="w+",
                encoding="utf-8"
            ) as file:
                file.write(response.text)

            yield Request(
                url=backup_code_url,
                headers=self.headers,
                dont_filter=True,
                callback=self.parse_backup_code
            )
            return

        # If account, success
        self.logger.info(
            "Code %s success." % code
        )
        yield from super().start_requests()
        self.write_backup_codes()

    def get_topic_id(self, url=None):
        topic_id = self.topic_pattern.findall(url)
        try:
            return topic_id[0]
        except Exception as err:
            return

    def parse_thread_date(self, thread_date):
        return datetime.strptime(
            thread_date[:-6],
            self.sitemap_datetime_format
        )

    def parse_thread_url(self, thread_url):
        return thread_url.replace(".vc", ".io")

    def parse(self, response):
        forums = response.xpath(
            '//h3[@class="node-title"]/a')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )
        sub_forums = response.xpath(
            '//ol[@class="node-subNodeFlatList"]/li/a')
        for sub_forum in sub_forums:
            url = sub_forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[@data-preview-url]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.get_topic_id(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id[0]}
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//div[@class="message-avatar-wrapper"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if self.base_url not in avatar_url:
                avatar_url = self.base_url + avatar_url
            user_id = avatar.xpath('@alt').extract_first()
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
            if os.path.exists(file_name):
                continue
            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta={
                    'file_name': file_name,
                    'user_id': user_id
                }
            )

        next_page = response.xpath(
            '//a[@class="pageNav-jump pageNav-jump--next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                headers=self.headers,
                callback=self.parse_thread,
                meta={'topic_id': topic_id}
            )

    def parse_avatar(self, response):
        file_name = response.meta['file_name']
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar for user {response.meta['user_id']} done..!")


class BHFIOScrapper(SiteMapScrapper):

    spider_class = BHFIOSpider
    request_delay = 0.8
    no_of_threads = 4
    site_name = 'bhf.io'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads
            }
        )
        return spider_settings


if __name__ == '__main__':
    run_spider('/Users/PathakUmesh/Desktop/BlackHatWorld')

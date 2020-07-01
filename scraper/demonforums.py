import os
import re
import scrapy
import uuid

from scrapy.http import Request, FormRequest
from scraper.base_scrapper import (
    BypassCloudfareSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.4
NO_OF_THREADS = 10

USER = 'Cyrax_011'
PASS = 'Night#India065'


class DemonForumsSpider(BypassCloudfareSpider):
    name = 'demonforums_spider'

    use_proxy = True
    proxy_countries = ['us', 'uk']

    handle_httpstatus_list = [403, 503]

    ip_check_xpath = "//text()[contains(.,\"Your IP\")]"

    rotation_tries = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = 'https://demonforums.net/'
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.pagination_pattern = re.compile(r'.*page=(\d+)')
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.process_login,
            dont_filter=True
        )

    def parse_captcha(self, response):
        ip_ban_check = response.xpath(
            self.ip_check_xpath
        ).extract_first()

        # Report bugs
        if "error code: 1005" in response.text:
            self.logger.info(
                "Ip for error 1005 code. Rotating."
            )
        elif ip_ban_check:
            self.logger.info(
                "%s has been permanently banned. Rotating." % ip_ban_check
            )

        if not self.use_proxy:
            return

        if self.rotation_tries < 20:
            self.rotation_tries += 1
            yield from self.start_requests()

    def process_login(self, response):

        if response.status == 403:
            yield from self.parse_captcha(response)
            return

        my_post_key = response.xpath(
            '//input[@name="my_post_key"]/@value').extract_first()
        if not my_post_key:
            return
        form_data = {
            'action': 'do_login',
            'url': '',
            'quick_login': '1',
            'my_post_key':  my_post_key,
            'quick_username': USER,
            'quick_password': PASS,
            'quick_remember': 'yes',
            'submit': 'Login',
        }
        login_url = 'https://demonforums.net/member.php'
        yield FormRequest(
            url=login_url,
            formdata=form_data,
            callback=self.parse,
            headers=response.request.headers,
            meta=response.meta,
            dont_filter=True
        )

    def parse(self, response):

        if response.status == 403:
            yield from self.parse_captcha(response)
            return

        yield Request(
            url=self.base_url,
            callback=self.parse_start,
            headers=response.request.headers,
            meta=response.meta,
            dont_filter=True
        )

    def parse_start(self, response):

        if response.status == 403:
            meta = response.meta.copy()
            tries = meta.get('tries', 1)
            if tries < 20:
                meta['tries'] = tries + 1
                yield Request(
                    url=self.base_url,
                    callback=self.parse_start,
                    headers=response.request.headers,
                    meta=meta,
                    dont_filter=True
                )
                return

        forums = response.xpath(
            '//a[contains(@href, "Forum-")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url
            # if 'Forum-Graphics--36' not in url:
            #     continue
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=response.request.headers,
                meta=response.meta,
            )

    def parse_forum(self, response):

        if response.status == 403:
            meta = response.meta.copy()
            tries = meta.get('tries', 1)
            if tries < 20:
                meta['tries'] = tries + 1
                yield Request(
                    url=response.url,
                    callback=self.parse_forum,
                    headers=response.request.headers,
                    meta=meta,
                    dont_filter=True
                )
                return

        self.logger.info('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//span[contains(@class, "subject_") and contains(@id, "tid_")]/a')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = str(
                int.from_bytes(
                    thread_url.replace('Thread-', '').encode('utf-8'),
                    byteorder='big'
                ) % (10 ** 7)
            )
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id)
            if os.path.exists(file_name):
                continue
            meta = response.meta
            meta.update({
                'topic_id': topic_id
            })
            yield Request(
                url=thread_url,
                callback=self.parse_thread,
                headers=response.request.headers,
                meta=meta
            )

        next_page = response.xpath(
            '//a[@class="pagination_next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                headers=response.request.headers,
                meta=response.meta
            )

    def parse_thread(self, response):

        if response.status == 403:
            meta = response.meta.copy()
            tries = meta.get('tries', 1)
            if tries < 20:
                meta['tries'] = tries + 1
                yield Request(
                    url=response.url,
                    callback=self.parse_forum,
                    headers=response.request.headers,
                    meta=meta,
                    dont_filter=True
                )
                return

        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        paginated_value = pagination[0] if pagination else 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            self.logger.info(f'{topic_id}-{paginated_value} done..!')

        avatars = response.xpath(
            '//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
            if 'svg+xml' in avatar_url:
                continue
            if not avatar_url.startswith('http'):
                avatar_url = self.base_url + avatar_url
            name_match = self.avatar_name_pattern.findall(avatar_url)
            if not name_match:
                continue
            name = name_match[0]
            file_name = '{}/{}'.format(self.avatar_path, name)
            if os.path.exists(file_name):
                continue
            meta = response.meta
            meta.update({
                'file_name': file_name
            })
            yield Request(
                url=avatar_url,
                callback=self.parse_avatar,
                headers=response.request.headers,
                meta=meta
            )

        next_page = response.xpath(
            '//div[@class="pagination"]'
            '/a[@class="pagination_next"]')
        meta = response.meta
        meta.update({
            'topic_id': topic_id
        })
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                headers=response.request.headers,
                meta=response.meta
            )

    def parse_avatar(self, response):

        if response.status == 403:
            meta = response.meta.copy()
            tries = meta.get('tries', 1)
            if tries < 20:
                meta['tries'] = tries + 1
                yield Request(
                    url=response.url,
                    callback=self.parse_forum,
                    headers=response.request.headers,
                    meta=meta,
                    dont_filter=True
                )
                return

        file_name = response.meta['file_name']
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            self.logger.info(f"Avatar {file_name_only} done..!")


class DemonForumsScrapper(SiteMapScrapper):

    spider_class = DemonForumsSpider
    site_name = 'demonforums.net'

    def load_settings(self):
        spider_settings = super().load_settings()
        spider_settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return spider_settings

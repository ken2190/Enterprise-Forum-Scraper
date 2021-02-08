import os
import re
import uuid

from urllib.parse import unquote

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"

PROXY = 'http://127.0.0.1:8118'


class HappyBlogSpider(SitemapSpider):

    name = "happyblog_spider"

    # Url stuffs
    base_url = "http://dnpscnbaix6nkwvystl3yxglz7nteicqrou3t75tpcc5532cztc46qyd.onion"

    current_page_xpath = '//li[@class="page-item active"]/a/text()'
    next_page_xpath = '//li[@class="page-item "]/a[contains(., "Next")]/@href'
    image_xpath = '//img[@class="item-image"]/@src'

    use_proxy = "Tor"

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

    def get_thread_current_page(self, response):
        current_page = response.xpath(
                self.current_page_xpath
        ).extract_first() or "1"
        return current_page.strip()

    def get_thread_next_page(self, response):
        next_page = response.xpath(self.next_page_xpath).extract_first()
        if not next_page:
            return

        next_page = next_page.strip()
        # process url if its not complete
        if 'http://' not in next_page and 'https://' not in next_page:
            temp_url = next_page

            if self.base_url not in next_page:
                temp_url = response.urljoin(next_page)

            if self.base_url not in temp_url:
                temp_url = self.base_url + next_page

            next_page = temp_url

        return next_page

    def get_avatar_file(self, url=None):
        """
        :param url: str => avatar url
        :return: str => extracted avatar file from avatar url
        """

        if getattr(self, "avatar_name_pattern", None):
            try:
                file_name = os.path.join(
                    self.avatar_path,
                    self.avatar_name_pattern.findall(url)[0]
                )
                extensions = ['jpg', 'jpeg', 'png', 'gif']
                for ext in extensions:
                    if ext in file_name.lower():
                        return file_name
                return f'{file_name}.jpg'
            except Exception as err:
                return

        return
        
    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta

    def start_requests(self):
        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", 1)
        self.crawler.stats.set_value("mainlist/detail_saved_count", 0)

        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse,
            errback=self.check_site_error,
            dont_filter=True,
            meta={
                'proxy': PROXY,
            }
        )

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        current_page = self.get_thread_current_page(response)
        print(current_page)
        # get next page
        next_page = self.get_thread_next_page(response)

        with open(
            file=os.path.join(
                self.output_path,
                "%s.html" % (
                    current_page
                )
            ),
            mode="w+",
            encoding="utf-8"
        ) as file:
            file.write(response.text)

        self.logger.info(
            f'{current_page} done..!'
        )
        self.crawler.stats.inc_value("mainlist/detail_saved_count")

        yield from self.parse_images(response)

        if next_page:
            yield Request(
                url=next_page,
                headers=self.headers,
                callback=self.parse,
                meta=self.synchronize_meta(
                    response
                )
            )

    def parse_images(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        all_avatars = set(response.xpath(self.image_xpath).extract())

        for avatar_url in all_avatars:
            # Standardize avatar url only if its not complete url
            slash = False
            if 'http://' not in avatar_url and 'https://' not in avatar_url:
                temp_url = avatar_url

                if avatar_url.startswith('//'):
                    slash = True
                    temp_url = avatar_url[2:]

                if not avatar_url.lower().startswith("http"):
                    temp_url = response.urljoin(avatar_url)

                if self.base_url not in temp_url and not slash:
                    temp_url = self.base_url + avatar_url

                avatar_url = temp_url

            if 'image/svg' in avatar_url:
                continue

            file_name = self.get_avatar_file(avatar_url)

            if file_name is None:
                continue

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_image,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )

    def parse_image(self, response):

        # Load file name
        file_name = response.meta.get("file_name")
        avatar_name = os.path.basename(file_name)

        # Save avatar
        with open(file_name, "wb") as f:
            f.write(response.body)
            self.logger.info(
                f"Image {avatar_name} done..!"
            )

class HappyBlogScrapper(SiteMapScrapper):
    spider_class = HappyBlogSpider
    site_name = 'happyblog'
    site_type = 'forum'

    def __init__(self, kwargs):
        super().__init__(kwargs)
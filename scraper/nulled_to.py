import os
import re
import uuid

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


FORUMS = [
    'https://www.nulled.to/forum/2-announcements/',
    'https://www.nulled.to/forum/209-releases/',
    'https://www.nulled.to/forum/110-feedback-and-suggestions/',
    'https://www.nulled.to/forum/32-support/',
    'https://www.nulled.to/forum/125-archive/',
    'https://www.nulled.to/forum/3-the-lounge/',
    'https://www.nulled.to/forum/114-crypto-currencies/',
    'https://www.nulled.to/forum/93-entertainment/',
    'https://www.nulled.to/forum/204-personal-life/',
    'https://www.nulled.to/forum/115-achievements-bragging/',
    'https://www.nulled.to/forum/62-gaming/',
    'https://www.nulled.to/forum/35-graphics/',
    'https://www.nulled.to/forum/7-cracked-programs/',
    'https://www.nulled.to/forum/43-accounts/',
    'https://www.nulled.to/forum/184-dumps-databases/',
    'https://www.nulled.to/forum/24-source-codes-scripts/',
    'https://www.nulled.to/forum/9-e-books-guides-and-tutorials/',
    'https://www.nulled.to/forum/15-other-leaks/',
    'https://www.nulled.to/forum/117-requests/',
    'https://www.nulled.to/forum/41-vip-general-chat/',
    'https://www.nulled.to/forum/42-vip-leaks/',
    'https://www.nulled.to/forum/44-vip-dumps/',
    'https://www.nulled.to/forum/90-cracking-tools/',
    'https://www.nulled.to/forum/98-cracking-tutorials-information/',
    'https://www.nulled.to/forum/91-cracking-support/',
    'https://www.nulled.to/forum/73-configs/',
    'https://www.nulled.to/forum/74-combolists/',
    'https://www.nulled.to/forum/49-proxies/',
    'https://www.nulled.to/forum/57-beginner-hacking/',
    'https://www.nulled.to/forum/99-advanced-hacking/',
    'https://www.nulled.to/forum/58-hacking-tutorials/',
    'https://www.nulled.to/forum/70-monetizing-techniques/',
    'https://www.nulled.to/forum/69-social-engineering/',
    'https://www.nulled.to/forum/201-e-whoring/',
    'https://www.nulled.to/forum/122-amazon/',
    'https://www.nulled.to/forum/51-visual-basic-and-net-framework/',
    'https://www.nulled.to/forum/52-cc-obj-c-programming/',
    'https://www.nulled.to/forum/55-assembly-language-and-programming/',
    'https://www.nulled.to/forum/53-java-language-jvm-and-the-jre/',
    'https://www.nulled.to/forum/54-phphtmlcsssql-development/',
    'https://www.nulled.to/forum/100-lua/',
    'https://www.nulled.to/forum/135-coding-and-programming/',
    'https://www.nulled.to/forum/157-marketplace-lobby/',
    'https://www.nulled.to/forum/60-premium-sellers/',
    'https://www.nulled.to/forum/46-secondary-sellers/',
    'https://www.nulled.to/forum/47-buyers/',
    'https://www.nulled.to/forum/61-trading-station/',
    'https://www.nulled.to/forum/195-service-requests/',
    'https://www.nulled.to/forum/171-archive/',
    'https://www.nulled.to/forum/11-general-chat/',
    'https://www.nulled.to/forum/12-reverse-engineering-guides-and-tips/',
    'https://www.nulled.to/forum/14-tools/',
    'https://www.nulled.to/forum/192-motm/',
    'https://www.nulled.to/forum/33-answered/',
    'https://www.nulled.to/forum/178-account-recovery/',
    'https://www.nulled.to/forum/132-ban-appeals/',
    'https://www.nulled.to/forum/134-hq-lounge/',
    'https://www.nulled.to/forum/5-introductions/',
    'https://www.nulled.to/forum/186-news-and-politics/',
    'https://www.nulled.to/forum/94-music/',
    'https://www.nulled.to/forum/95-movies-series/',
    'https://www.nulled.to/forum/97-leaks/',
    'https://www.nulled.to/forum/66-league-of-legends/',
    'https://www.nulled.to/forum/208-fortnite/',
    'https://www.nulled.to/forum/64-fps/',
    'https://www.nulled.to/forum/63-mmo/',
    'https://www.nulled.to/forum/101-other-games/',
    'https://www.nulled.to/forum/126-graphic-resources/',
    'https://www.nulled.to/forum/36-paid-graphic-work/',
    'https://www.nulled.to/forum/18-mmo-bots/',
    'https://www.nulled.to/forum/19-moba-bots/',
    'https://www.nulled.to/forum/149-youtube-twitter-and-fb-bots/',
    'https://www.nulled.to/forum/20-malicious-software/',
    'https://www.nulled.to/forum/21-miscellaneous/',
    'https://www.nulled.to/forum/30-exploits/',
    'https://www.nulled.to/forum/25-ccobj-c/',
    'https://www.nulled.to/forum/27-net-framework/',
    'https://www.nulled.to/forum/29-php-css-jvscript/',
    'https://www.nulled.to/forum/198-combos/',
    'https://www.nulled.to/forum/199-accounts/',
    'https://www.nulled.to/forum/210-openbullet/',
    'https://www.nulled.to/forum/211-sentry-mba/',
    'https://www.nulled.to/forum/212-blackbullet/',
    'https://www.nulled.to/forum/213-storm/',
    'https://www.nulled.to/forum/214-snipr/',
    'https://www.nulled.to/forum/188-dorks/',
    'https://www.nulled.to/forum/59-website-and-forum-hacking/',
    'https://www.nulled.to/forum/145-resources/',
    'https://www.nulled.to/forum/146-discussion/',
    'https://www.nulled.to/forum/147-help/',
    'https://www.nulled.to/forum/148-tutorials/',
    'https://www.nulled.to/forum/137-c/',
    'https://www.nulled.to/forum/136-net-leaks-downloads/',
    'https://www.nulled.to/forum/139-cc-leaks-downloads/',
    'https://www.nulled.to/forum/141-java-leaks-downloads/',
    'https://www.nulled.to/forum/140-php-leaks-downloads/',
    'https://www.nulled.to/forum/142-other-leaks/',
    'https://www.nulled.to/forum/159-scam-reports/',
    'https://www.nulled.to/forum/129-products/',
    'https://www.nulled.to/forum/128-accounts/',
    'https://www.nulled.to/forum/127-services/',
    'https://www.nulled.to/forum/160-e-books-monetizing-guides/',
    'https://www.nulled.to/forum/161-combos-configs/',
    'https://www.nulled.to/forum/177-accounts/',
    'https://www.nulled.to/forum/163-products/',
    'https://www.nulled.to/forum/164-services/',
    'https://www.nulled.to/forum/191-graphics-marketplace/',
    'https://www.nulled.to/forum/165-currency-exchange/',
    'https://www.nulled.to/forum/196-partnership-hiring/',
    'https://www.nulled.to/forum/197-favors-rewards/',
]


class NulledSpider(SitemapSpider):
    name = 'nulled_spider'

    # Url stuffs
    base_url = "https://www.nulled.to"
    start_url = 'https://www.nulled.to'

    # Xpath stuffs
    thread_xpath = "//tr[contains(@id,\"trow\")]"
    thread_date_xpath = "//td[@class=\"col_f_post\"]/ul/li[contains(@class,\"blend_links\")]/a/text()"
    thread_url_xpath = "//ul[contains(@class,\"mini_pagination\")]/li[last()]/a/@href|" \
                       "//a[@itemprop=\"url\" and contains(@id, \"tid-link-\")]/@href"

    pagination_xpath = "//li[@class=\"next\"]/a/@href"
    thread_pagination_xpath = "//li[@class=\"prev\"]/a/@href"
    thread_page_xpath = "//li[@class=\"page active\"]/text()"
    post_date_xpath = "//div[@class=\"post_body\"]/div[@class=\"post_date\"]/abbr[@class=\"published\"]/@title"
    avatar_xpath = "//li[@class=\"avatar\"]/img/@src"

    # Regex stuffs
    topic_pattern = re.compile(
        r"topic/(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    sitemap_datetime_format = "%d %b, %Y"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {
                "Referer": "https://www.nulled.to/",
                "Sec-fetch-mode": "navigate",
                "Sec-fetch-site": "none",
                "Sec-fetch-user": "?1",
            }
        )

    def parse_thread_date(self, thread_date):
        if "Today" in thread_date:
            return datetime.today()
        elif "Yesterday" in thread_date:
            return datetime.today() - timedelta(days=1)
        return datetime.strptime(
            thread_date.strip(),
            self.sitemap_datetime_format
        )

    def parse_post_date(self, post_date):
        return datetime.strptime(
            post_date.strip()[:-6],
            self.post_datetime_format
        )

    def start_requests(self):
        # Proceed for banlist
        if not self.avatar_path:
            ban_url = 'https://www.nulled.to/ban-list.php'
            yield Request(
                url=ban_url,
                headers=self.headers,
                callback=self.parse_ban_list,
                meta={'pagination': 1}
            )
        else:
            for forum_url in FORUMS:
                yield Request(
                    url=forum_url,
                    headers=self.headers,
                    callback=self.parse_forum,
                    meta={
                        "cookiejar": uuid.uuid1().hex
                    }
                )

    def parse_ban_list(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Load pagination
        pagination = response.meta.get("pagination")

        # Write content
        file_name = "%s/page-%s.html" % (
            self.output_path,
            pagination
        )
        with open(file_name, "wb") as f:
            f.write(response.text.encode("utf-8"))
            self.logger.info(
                "page-%s done..!" % pagination
            )
            
        # Pagination
        last_page = response.xpath("//li[@class=\"last\"]/a")
        if last_page and pagination == 1:
            last_page_index = last_page.xpath("@href").re(r"st=(\d+)")
            for st in range(50, int(last_page_index[0]) + 50, 50):
                url = "https://www.nulled.to/ban-list.php?&st=%s" % st
                pagination += 1
                yield Request(
                    url=url,
                    headers=self.headers,
                    callback=self.parse_ban_list,
                    meta=self.synchronize_meta(
                        response,
                        default_meta={
                            "pagination": pagination
                        }
                    )
                )

    def parse_thread(self, response):

        # Save avatar content
        yield from super().parse_avatars(response)

        # Parse generic thread response
        yield from super().parse_thread(response)


class NulledToScrapper(SiteMapScrapper):

    request_delay = 0.4
    no_of_threads = 10
    spider_class = NulledSpider

    def __init__(self, kwargs):
        super().__init__(kwargs)
        if kwargs.get('banlist'):
            self.ensure_ban_path()

    def ensure_ban_path(self, ):
        self.banlist_path = f'{self.output_path}/banlist'
        if not os.path.exists(self.banlist_path):
            os.makedirs(self.banlist_path)

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': self.request_delay,
                'CONCURRENT_REQUESTS': self.no_of_threads,
                'CONCURRENT_REQUESTS_PER_DOMAIN': self.no_of_threads,
                'RETRY_HTTP_CODES': [403, 429, 500, 503, 504],
            }
        )
        return settings


if __name__ == "__main__":
    pass

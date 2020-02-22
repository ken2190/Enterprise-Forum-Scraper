import re

from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class ScrapeBoxForumSpider(SitemapSpider):
    name = "scrapeboxforum_spider"
    
    # Url stuffs
    base_url = "https://scrapeboxforum.com/"

    # Xpath stuffs
    forum_xpath = "//td[contains(@class,\"trow\")]/strong/a/@href"
    pagination_xpath = "//a[@class=\"pagination_next\"]/@href"

    thread_xpath = "//tr[@class=\"inline_row\"]"
    thread_first_page_xpath = "//span[contains(@id,\"tid\")]/a/@href"
    thread_last_page_xpath = "//span[contains(@id,\"tid\")]/following-sibling::span/a[last()]/@href"
    thread_date_xpath = "//span[@class=\"lastpost smalltext\"]/text()[contains(.,\"-\")]|" \
                        "//span[@class=\"lastpost smalltext\"]/span[@title]"

    thread_pagination_xpath = "//a[@class=\"pagination_previous\"]/@href"
    thread_page_xpath = "//span[@class=\"pagination_current\"]/text()"
    post_date_xpath = "//span[@class=\"post_date\"]/text()[contains(.,\"-\")]|" \
                      "//span[@class=\"post_date\"]/span[@title]/@title"
    avatar_xpath = "//div[@class=\"author_avatar\"]/a/img/@src"
    
    # Regex stuffs
    topic_pattern = re.compile(
        r"tid=(\d+)",
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

    def parse(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?fid=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
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
            '//a[contains(@href, "showthread.php?tid=")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
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

        next_page = response.xpath('//a[@class="pagination_next"]')
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

        avatars = response.xpath('//div[@class="author_avatar"]/a/img')
        for avatar in avatars:
            avatar_url = avatar.xpath('@src').extract_first()
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
                    'file_name': file_name
                }
            )

        next_page = response.xpath('//a[@class="pagination_next"]')
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
        file_name_only = file_name.rsplit('/', 1)[-1]
        with open(file_name, 'wb') as f:
            f.write(response.body)
            print(f"Avatar {file_name_only} done..!")


class ScrapeBoxForumScrapper(SiteMapScrapper):

    spider_class = ScrapeBoxForumSpider


if __name__ == "__main__":
    pass

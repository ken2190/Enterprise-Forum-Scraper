import re
import os
import time
import random
import traceback
from scraper.base_scrapper import BaseScrapper


# Topic Counter
TOPIC_START_COUNT = 641000
TOPIC_END_COUNT = 641200

data = {
    "login": "darkcylon1@protonmail.com",
    "password": "Night#Kgg2",
    "remember": "1",
    "stop_brute_pls": "1",
    "cookie_check": "1",
    "_xfToken": "",
}

headers = {
    "TE": "Trailers",
    "Host": "lolzteam.net",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0",

}


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Cookie": "xf_id=2f6539f788522e5b59f8bcaaaf47afef; G_ENABLED_IDPS=google; xf_session=8834fa672a7f69c7abda0e48a59eca13",
    "Host": "lolzteam.net",
    "If-Modified-Since": "Sun, 13 Jan 2019 14:56:01 GMT",
    "TE": "Trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0",

}


class LolzScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(LolzScrapper, self).__init__(kwargs)
        self.site_link = "https://lolzteam.net/"
        self.topic_url = self.site_link + "threads/{}/"
        self.headers.update({
            'cookie': 'xf_id=2c8efa5f8dde7b8207cbb79da37a5bbe'
        })
        self.ignore_xpath = '//div[@class="titleBar"]/'\
                            'h1[@title="Error"]'

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//nav/a[contains(@class,"currentPage")]'
            '/following-sibling::span[1][@class="scrollable"]'
            '//a/@href'
        )
        if not next_page_block:
            next_page_block = html_response.xpath(
                '//a[contains(@class,"currentPage")]'
                '/following-sibling::a[1]/@href'
            )
        if not next_page_block:
            next_page_block = html_response.xpath(
                '//nav/span[@class="scrollable"][span'
                '/a[contains(@class,"currentPage")]]'
                '/following-sibling::a[2]/@href'
            )

        if not next_page_block:
            return
        next_page_url = self.site_link + next_page_block[0]\
            if self.site_link not in next_page_block[0]\
            else next_page_block[0]
        pattern = re.compile(r"threads/(\d+)/page-(\d+)")
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]

        content = self.get_page_content(
            next_page_url, self.ignore_xpath
        )
        if not content:
            return

        paginated_file = '{}/{}-{}.html'.format(
            self.output_path, topic, pagination_value
        )
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print('{}-{} done..!'.format(topic, pagination_value))
        return content

    def clear_cookies(self,):
        self.session.cookies['topicsread'] = ''

    def do_scrape(self):
        print('**************  LolzTeam Scrapper Started  **************\n')
        ts = self.topic_start_count or TOPIC_START_COUNT
        te = self.topic_end_count or TOPIC_END_COUNT + 1
        topic_list = list(range(ts, te))
        # random.shuffle(topic_list)
        for topic in topic_list:
            try:
                response = self.process_first_page(
                    topic, self.ignore_xpath
                )
                if response is None:
                    continue

                # ------------clear cookies without logout--------------
                self.clear_cookies()
            except:
                traceback.print_exc()
                continue
            self.process_pagination(response)


def main():
    template = LolzScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

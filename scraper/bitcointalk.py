import re
import os
import time
import random
import traceback
from scraper.base_scrapper import BaseScrapper


# Topic Counter
TOPIC_START_COUNT = 5032000
TOPIC_END_COUNT = 5033000


class BitCoinTalkScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(BitCoinTalkScrapper, self).__init__(kwargs)
        self.topic_url = "https://bitcointalk.org/index.php?topic={}.0"
        self.ignore_xpath = \
            '//td[contains(text(),'\
            '"The topic or board you are looking for appears to '\
            'be either missing or off limits to you")]'
        self.continue_xpath = '//h1[contains(text(),"Too fast / overloaded")]'
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//td[@class="middletext"]/b[not(contains(text(), "..."))]'
            '/following-sibling::a[1][@class="navPages"]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        pattern = re.compile(r"topic=(\d+)\.(\d+)")
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]

        content = self.get_page_content(
            next_page_url, self.ignore_xpath, self.continue_xpath
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

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        # urls = html_response.xpath(
        #     '//div[@class="author_avatar"]/a/img/@src'
        # )
        # for url in urls:
        #     name_match = self.avatar_name_pattern.findall(url)
        #     if not name_match:
        #         continue
        #     name = name_match[0]
        #     if name not in avatar_info:
        #         avatar_info.update({
        #             name: url
        #         })
        return avatar_info

    def do_scrape(self):
        print('**************  BitCoinTalk Scrapper Started  **************\n')
        # ----------------go to topic ------------------
        ts = self.topic_start_count or TOPIC_START_COUNT
        te = self.topic_end_count or TOPIC_END_COUNT + 1
        topic_list = list(range(ts, te))
        random.shuffle(topic_list)
        for topic in topic_list:
            try:
                response = self.process_first_page(
                    topic, self.ignore_xpath, self.continue_xpath
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
    template = BitCoinTalkScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

import re
import os
import time
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

    def do_scrape(self):
        print('**************  BitCoinTalk Scrapper Started  **************\n')
        # ----------------go to topic ------------------
        for topic in range(self.topic_start_count, self.topic_end_count):
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

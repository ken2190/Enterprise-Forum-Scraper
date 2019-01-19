import re
import os
import time
import traceback
from requests import Session
from lxml.html import fromstring


# Topic Counter
TOPIC_START_COUNT = 5032800
TOPIC_END_COUNT = 5032900


class BitCoinTalkScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))
        self.topic_end_count = int(kwargs.get('topic_end')) + 1
        self.topic_url = "https://bitcointalk.org/index.php?topic={}.0"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'
        }
        self.session = Session()
        self.output_path = kwargs.get('output')

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def get_page_content(self, url):
        time.sleep(1)
        try:
            response = self.session.get(url, headers=self.headers)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath(
               '//td[contains(text(),'
               '"The topic or board you are looking for appears to '
               'be either missing or off limits to you")]'):
                return
            if html_response.xpath(
               '//h1[contains(text(),"Too fast / overloaded")]'):
                return get_page_content(self, url)
            return content
        except:
            return

    def process_first_page(self, topic):
        initial_file = '{}/{}.html'.format(self.output_path, topic)
        if os.path.exists(initial_file):
            return
        url = self.topic_url.format(topic)
        content = self.get_page_content(url)
        if not content:
            print('No data for url: {}'.format(url))
            return
        with open(initial_file, 'wb') as f:
            f.write(content)
        print('{} done..!'.format(topic))
        html_response = self.get_html_response(content)
        return html_response

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//td[@class="middletext"]/b'
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

        content = self.get_page_content(next_page_url)
        if not content:
            return

        paginated_file = '{}/{}-{}.html'.format(
            self.output_path, topic, pagination_value
        )
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print('{}-{} done..!'.format(topic, pagination_value))
        return content

    def process_pagination(self, response):
        while True:
            paginated_content = self.write_paginated_data(response)
            if not paginated_content:
                return
            response = self.get_html_response(paginated_content)

    def clear_cookies(self,):
        self.session.cookies['topicsread'] = ''

    def do_scrape(self):
        print('**************  BitCoinTalk Scrapper Started  **************\n')
        # ----------------go to topic ------------------
        for topic in range(self.topic_start_count, self.topic_end_count):
            try:
                response = self.process_first_page(topic)
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

import re
import os
import time
import traceback
from requests import Session
from lxml.html import fromstring


# Topic Counter
TOPIC_START_COUNT = 550001
TOPIC_END_COUNT = 763158


class LolzScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = TOPIC_START_COUNT
        self.topic_end_count = TOPIC_END_COUNT
        self.site_link = "https://lolzteam.net/"
        self.topic_url = self.site_link + "threads/{}/"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
            'cookie': 'xf_id=f60b62ee46a315a39be744c1ef0b50a6'
        }
        self.session = Session()
        self.output_path = kwargs.get('output')
        if kwargs.get('proxy'):
            self.session.proxies = {}
            self.session.proxies['http'] = kwargs.get('proxy')
            self.session.proxies['https'] = kwargs.get('proxy')

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def get_page_content(self, url):
        time.sleep(0.5)
        try:
            response = self.session.get(url, headers=self.headers)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath(
               '//label[contains(text(),'
               '"The requested thread could not be found")]'):
                return
            if html_response.xpath(
               '//div[@class="titleBar"]/'
               'h1[@title="Error"]'):
                return
            return content
        except:
            return

    def process_first_page(self, topic):
        url = self.topic_url.format(topic)
        content = self.get_page_content(url)
        if not content:
            print('No data for url: {}'.format(url))
            return
        initial_file = '{}/{}.html'.format(self.output_path, topic)
        with open(initial_file, 'wb') as f:
            f.write(content)
        print('{} done..!'.format(topic))
        html_response = self.get_html_response(content)
        return html_response

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
        print('**************  LolzTeam Scrapper Started  **************\n')
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
    template = LolzScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

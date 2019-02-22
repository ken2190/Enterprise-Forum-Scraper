import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper


class CCCMNScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(CCCMNScrapper, self).__init__(kwargs)
        self.base_url = 'http://ccc.mn/index.php'
        self.topic_pattern = re.compile(r'/topic/(\d+)-')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.cloudfare_error = None

    def get_page_content(self, url):
        time.sleep(self.wait_time)
        try:
            response = requests.get(url)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath('//div[@class="errorwrap"]'):
                return
            return content
        except:
            return

    def save_avatar(self, name, url):
        avatar_file = f'{self.avatar_path}/{name}'
        if os.path.exists(avatar_file):
            return
        content = self.get_page_content(url)
        if not content:
            return
        with open(avatar_file, 'wb') as f:
            f.write(content)

    def process_first_page(self, topic_url):
        topic = self.topic_pattern.findall(topic_url)
        if not topic:
            return
        topic = topic[0]
        initial_file = f'{self.output_path}/{topic}-1.html'
        if os.path.exists(initial_file):
            return
        content = self.get_page_content(topic_url)
        if not content:
            print(f'No data for url: {topic_url}')
            return
        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
        html_response = self.get_html_response(content)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return html_response

    def process_topic(self, topic_url):
        html_response = self.process_first_page(topic_url)
        if html_response is None:
            return
        while True:
            response = self.write_paginated_data(html_response)
            if response is None:
                return
            topic_url, html_response = response

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//ul[@class="ipsList_inline forward left"]'
            '/li[@class="next"]/a/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        pattern = re.compile(r'/topic/(\d+)-.*/page__st__(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        content = self.get_page_content(next_page_url)
        if not content:
            return
        pagination_value = int(int(pagination_value)/20 + 1)
        paginated_file = f'{self.output_path}/{topic}-{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}-{pagination_value} done..!')
        html_response = self.get_html_response(content)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return next_page_url, html_response

    def process_forum(self, url):
        while True:
            print(f"Forum URL: {url}")
            forum_content = self.get_page_content(url)
            if not forum_content:
                print(f'No data for url: {forum_content}')
                return
            html_response = self.get_html_response(forum_content)
            topic_urls = html_response.xpath(
                '//td[contains(@class, "col_f_content")]/h4/a/@href')
            for topic_url in topic_urls:
                self.process_topic(topic_url)
            forum_pagination_url = html_response.xpath(
                '//ul[@class="ipsList_inline forward left"]'
                '/li[@class="next"]/a/@href'
            )
            if not forum_pagination_url:
                return
            url = forum_pagination_url[0]

    def get_forum_urls(self, html_response):
        extracted_urls = html_response.xpath(
            '//td[@class="col_c_forum"]/h4/a/@href')
        return extracted_urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//li[@class="avatar"]/a/img/@src'
        )
        for url in urls:
            name_match = self.avatar_name_pattern.findall(url)
            if not name_match:
                continue
            name = name_match[0]
            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def do_scrape(self):
        print('**************  CCCMN Scrapper Started  **************\n')
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        html_response = self.get_html_response(main_content)
        forum_urls = self.get_forum_urls(html_response)
        # print(forum_urls)
        # return
        # forum_urls = ["http://www.badkarma.ru/forums/veschevoj-karding.68/"]
        for forum_url in forum_urls:
            self.process_forum(forum_url)


def main():
    template = CCCMNScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

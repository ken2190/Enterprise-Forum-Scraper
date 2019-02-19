import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper


class SinisterScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(SinisterScrapper, self).__init__(kwargs)
        self.base_url = 'https://sinister.ly/'
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
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
        topic = topic_url.replace(self.base_url, '').replace('Thread-', '')
        initial_file = f'{self.output_path}/{topic}--1.html'
        if os.path.exists(initial_file):
            return
        content = self.get_page_content(topic_url)
        if not content:
            print(f'No data for url: {topic_url}')
            return
        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}--1 done..!')
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
            '//span[@class="pagination_current"]'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        next_page_url = self.base_url + next_page_url\
            if self.base_url not in next_page_url else next_page_url
        pattern = re.compile(r'sinister\.ly/(.*)\?page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        topic = topic.replace('Thread-', '')
        content = self.get_page_content(next_page_url)
        if not content:
            return
        paginated_file = f'{self.output_path}/{topic}--{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}--{pagination_value} done..!')
        html_response = self.get_html_response(content)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return next_page_url, html_response

    def process_forum(self, url):
        while True:
            print(f"Forum URL: {url}")
            print('-------------------------------------------------\n')
            forum_content = self.get_page_content(url)
            if not forum_content:
                print(f'No data for url: {forum_content}')
                return
            html_response = self.get_html_response(forum_content)
            topic_blocks = html_response.xpath(
                '//span[contains(@class, "subject_new")]/a/@href')
            if not topic_blocks:
                return
            for topic_url in topic_blocks:
                topic_url = self.base_url + topic_url\
                    if self.base_url not in topic_url else topic_url
                self.process_topic(topic_url)
            forum_pagination_url = html_response.xpath(
                '//span[@class="pagination_current"]'
                '/following-sibling::a[1]/@href'
            )
            if not forum_pagination_url:
                return
            url = forum_pagination_url[0]
            url = self.base_url + url\
                if self.base_url not in url else url

    def get_forum_urls(self, html_response):
        urls = list()
        extracted_urls = html_response.xpath(
            '//td[(@class="trow1" or @class="trow2") and @valign="top"]'
            '/strong/a/@href'
        )
        for _url in extracted_urls:
            if self.base_url not in _url:
                urls.append(self.base_url + _url)
            else:
                urls.append(_url)
        return urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//div[@class="author_avatar postbit_avatar"]/a/img/@src'
        )
        for url in urls:
            url = self.base_url + url\
                if self.base_url not in url else url
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
        print('**************  Sinister Scrapper Started  **************\n')
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        html_response = self.get_html_response(main_content)
        forum_urls = self.get_forum_urls(html_response)
        # forum_urls = ["http://www.badkarma.ru/forums/veschevoj-karding.68/"]
        for forum_url in forum_urls:
            self.process_forum(forum_url)


def main():
    template = SinisterScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper


class BlackBoxScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(BlackBoxScrapper, self).__init__(kwargs)
        self.base_url = 'http://blackboxs.biz/'
        self.topic_pattern = re.compile(r't=(\d+)')
        self.comment_pattern = re.compile(r'(\<\!--.*?--\!\>)')
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
            traceback.print_exc()
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
        content = self.comment_pattern.sub('', str(content))
        html_response = self.get_html_response(content)
        if html_response.xpath(
            '//font[contains(text(), "Verifying your browser, please wait")]'
        ):
            print('DDOS identified. Retyring after a min')
            time.sleep(60)
            return self.process_first_page(topic_url)
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
            '//a[@rel="next"]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        next_page_url = self.base_url + next_page_url\
            if self.base_url not in next_page_url else next_page_url
        pattern = re.compile(r't=(\d+)&page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        content = self.get_page_content(next_page_url)
        if not content:
            return
        paginated_file = f'{self.output_path}/{topic}-{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}-{pagination_value} done..!')
        content = self.comment_pattern.sub('', str(content))
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
            forum_content = self.comment_pattern.sub('', str(forum_content))
            html_response = self.get_html_response(forum_content)
            topic_urls = html_response.xpath(
                '//table[@id="threadslist"]//td[@id]'
                '//a[contains(@href, "showthread.php")]/@href'
            )
            for topic_url in topic_urls:
                topic_url = self.base_url + topic_url\
                    if self.base_url not in topic_url else topic_url
                self.process_topic(topic_url)
            forum_pagination_url = html_response.xpath(
                '//a[@rel="next"]/@href'
            )
            if not forum_pagination_url:
                return
            url = forum_pagination_url[0]
            url = self.base_url + url\
                if self.base_url not in url else url

    def get_forum_urls(self, html_response):
        urls = set()
        extracted_urls = html_response.xpath(
            '//td[@class="alt1Active"]'
            '//a[contains(@href, "forumdisplay.php")]/@href'
        )
        for _url in extracted_urls:
            if self.base_url not in _url:
                urls.add(self.base_url + _url)
            else:
                urls.add(_url)
        urls = sorted(
            urls,
            key=lambda x: int(x.split('f=')[-1]))
        return urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//td[@class="alt2"]/div[@class="smallfont"]/a/img/@src'
        )
        for url in urls:
            url = self.base_url + url\
                if not url.startswith('http') else url
            if "image.php" in url:
                avatar_name_pattern = re.compile(r'u=(\d+)')
                name_match = avatar_name_pattern.findall(url)
                if not name_match:
                    continue
                name = f'{name_match[0]}.jpg'
            else:
                avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
                name_match = avatar_name_pattern.findall(url)
                if not name_match:
                    continue
                name = name_match[0]

            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def do_scrape(self):
        print('************  BlackBoxScrapper Started  ************\n')
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        html_response = self.get_html_response(main_content)
        forum_urls = self.get_forum_urls(html_response)
        # print(forum_urls)
        # return
        # forum_urls = ['http://carder.me/forumdisplay.php?f=8']
        for forum_url in forum_urls:
            self.process_forum(forum_url)


def main():
    template = BlackBoxScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper
from scraper.sentryMBA import SentryMBAScrapper


USERNAME = "x23"
PASSWORD = "Night#Sentry99"


class SentryMBAv2Scrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(SentryMBAv2Scrapper, self).__init__(kwargs)
        self.base_url = 'https://sentry.mba/'
        self.login_url = self.base_url + "/member.php"
        self.topic_pattern = re.compile(r'tid=(\d+)')
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.cloudfare_error = '//h2[text()="Bad gateway"]'
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/72.0.3626.109 Safari/537.36",
            'referer': 'https://sentry.mba/member.php?action=login',
            'origin': 'https://sentry.mba',
        }
        self.kwargs = kwargs

    def get_page_content(self, url):
        time.sleep(self.wait_time)
        try:
            response = self.session.get(url, headers=self.headers)
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
        html_response = self.get_html_response(content)
        if html_response.xpath(self.cloudfare_error):
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!! Cloudfare Error Occurrred !!')
            print(f'URL:{topic_url}')
            print('Initializing Session again')
            self.session = Session()
            self.login()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return self.process_first_page(topic_url)
        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
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

        pattern = re.compile(r'tid=(\d+)&page=(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        content = self.get_page_content(next_page_url)
        if not content:
            return
        new_html_response = self.get_html_response(content)
        if new_html_response.xpath(self.cloudfare_error):
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('!! Cloudfare Error Occurrred !!')
            print(f'URL:{next_page_url}')
            print('Initializing Session again')
            self.session = Session()
            self.login()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return self.write_paginated_data(html_response)
        paginated_file = f'{self.output_path}/{topic}-{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}-{pagination_value} done..!')
        avatar_info = self.get_avatar_info(new_html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return next_page_url, new_html_response

    def process_forum(self, url):
        while True:
            print(f"Forum URL: {url}")
            forum_content = self.get_page_content(url)
            if not forum_content:
                print(f'No data for url: {forum_content}')
                return
            html_response = self.get_html_response(forum_content)
            topic_urls = html_response.xpath(
                '//div[@class="middle-table pad10"]//span[@id]/a/@href')
            for topic_url in topic_urls:
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
        urls = set()
        extracted_urls = list()
        forum_blocks = html_response.xpath(
            '//div[@class="forumstring"]'
            '/div[@class="row name p10"]')

        for block in forum_blocks:
            extracted_urls.extend(block.xpath('a/@href'))
            sub_blocks = block.xpath('div/div[@class="subform"]')

            for sub_block in sub_blocks:
                extracted_urls.extend(sub_block.xpath('a/@href'))

        for _url in extracted_urls:
            if self.base_url not in _url:
                urls.add(self.base_url + _url)
            else:
                urls.add(_url)
        return urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//img[@class="avatarp radius100"]/@src'
        )
        for url in urls:
            url = self.base_url + url\
                if not url.startswith('http') else url
            name_match = self.avatar_name_pattern.findall(url)
            if not name_match:
                continue
            name = name_match[0]
            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def login(self):
        url = "https://sentry.mba/member.php?action=login"
        content = self.get_page_content(url)
        if not content:
            print(f'No data for url: {content}')
            return
        html_response = self.get_html_response(content)
        my_post_key = html_response.xpath(
            '//input[@name="my_post_key"]/@value')
        if not my_post_key:
            return
        if not self.username:
            self.username = USERNAME
        if not self.password:
            self.password = PASSWORD
        payload = {
            "username": self.username,
            "password": self.password,
            "2facode": "",
            "remember": "",
            "submit": "Submit",
            "action": "do_login",
            "url": "https://sentry.mba/index.php",
            "my_post_key": my_post_key[0],
        }
        login_response = self.session.post(
            self.login_url,
            headers=self.headers,
            data=payload
        )
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath(
           '//div[contains(text(), "Authorization code mismatch")]'):
            return
        return True

    def do_new_posts_scrape(self,):
        print('**************  New posts scan  **************')
        if not self.login():
            print('Login failed! Exiting...')
            return
        print('Login Successful!')
        new_posts_url = self.base_url + "/search.php?action=getdaily"
        main_content = self.get_page_content(self.base_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        self.headers.update({
            'referer': self.headers['origin']
        })
        main_content = self.get_page_content(new_posts_url)
        if not main_content:
            print(f'No data for url: {self.base_url}')
            return
        html_response = self.get_html_response(main_content)
        topic_urls = html_response.xpath(
            '//div[@class="row p10"]/span/a[@id]/@href')
        for topic_url in topic_urls:
            topic_url = self.base_url + topic_url\
                if self.base_url not in topic_url else topic_url
            self.process_topic(topic_url)

    def do_rescan(self,):
        SentryMBAScrapper(self.kwargs).do_rescan()

    def do_scrape(self):
        print('**************  Sentry MBA Scrapper Started  **************\n')
        if not self.login():
            print('Login failed! Exiting...')
            return
        print('Login Successful!')
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
    template = SentryMBAv2Scrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

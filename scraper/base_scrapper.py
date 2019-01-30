import traceback
import os
import time
from requests import Session
from lxml.html import fromstring


class BaseScrapper:
    def __init__(self, kwargs):
        self.topic_start_count = int(kwargs.get('topic_start'))
        self.topic_end_count = int(kwargs.get('topic_end')) + 1
        self.output_path = kwargs.get('output')
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'
        }
        self.session = Session()
        if kwargs.get('proxy'):
            self.session.proxies = {
                'http': kwargs.get('proxy'),
                'https': kwargs.get('proxy'),
            }
        self.avatar_name_pattern = None
        self.cloudfare_error = None
        self.ensure_avatar_path()

    def ensure_avatar_path(self, ):
        self.avatar_path = '{}/avatars'.format(self.output_path)
        if not os.path.exists(self.avatar_path):
            os.makedirs(self.avatar_path)

    def get_html_response(self, content):
        html_response = fromstring(content)
        return html_response

    def get_page_content(self, url, ignore_xpath=None, continue_xpath=None):
        time.sleep(1)
        try:
            response = self.session.get(url, headers=self.headers)
            content = response.content
            html_response = self.get_html_response(content)
            if ignore_xpath and html_response.xpath(ignore_xpath):
                return
            if continue_xpath and html_response.xpath(continue_xpath):
                return self.get_page_content(
                    url, ignore_xpath, continue_xpath)
            if self.cloudfare_error and html_response.xpath(self.cloudfare_error):
                if self.cloudfare_count < 5:
                    self.cloudfare_count += 1
                    time.sleep(60)
                    return self.get_page_content(
                        url, ignore_xpath, continue_xpath)
                else:
                    return
            return content
        except:
            return

    def process_user_profile(
        self,
        uid,
        url,
    ):
        output_file = '{}/UID-{}.html'.format(self.output_path, uid)
        if os.path.exists(output_file):
            return
        content = self.get_page_content(url)
        if not content:
            return
        with open(output_file, 'wb') as f:
            f.write(content)
        print('UID-{} done..!'.format(uid))
        return

    def process_first_page(
        self,
        topic,
        ignore_xpath=None,
        continue_xpath=None
    ):
        self.cloudfare_count = 0
        initial_file = '{}/{}.html'.format(self.output_path, topic)
        if os.path.exists(initial_file):
            return
        url = self.topic_url.format(topic)
        content = self.get_page_content(url, ignore_xpath, continue_xpath)
        if not content:
            print('No data for url: {}'.format(url))
            return

        with open(initial_file, 'wb') as f:
            f.write(content)
        print('{} done..!'.format(topic))
        html_response = self.get_html_response(content)
        return html_response

    def process_pagination(self, response):
        while True:
            paginated_content = self.write_paginated_data(response)
            if not paginated_content:
                return
            response = self.get_html_response(paginated_content)
            avatar_info = self.get_avatar_info(response)
            for name, url in avatar_info.items():
                self.save_avatar(name, url)

    def save_avatar(self, name, url):
        avatar_file = '{}/{}'.format(self.avatar_path, name)
        if os.path.exists(avatar_file):
            return
        try:
            response = self.session.get(url, headers=self.headers)
        except:
            return
        if not response.status_code == 200:
            return
        content = response.content
        with open(avatar_file, 'wb') as f:
            f.write(content)

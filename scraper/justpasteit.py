import re
import os
import time
import requests
import datetime
import string
import traceback
import itertools
from lxml.html import fromstring

PROXY = "1.2.3.4:8080"


def get_keywords():
        keywords = [
            ''.join(i) for i in itertools.product(
                string.ascii_lowercase+string.digits, repeat=5)
        ]
        return keywords


def get_text(tag):
    text = tag.xpath(
        '//div[@id="articleContent"]'
        '/div/descendant::text()'
    )
    text = "\n".join(
        [txt.strip() for txt in text]
    ) if text else ""
    return text


class JustPasteItScrapper:
    def __init__(self, kwargs):
        self.base_url = 'https://justpaste.it/{}'
        self.output_path = kwargs.get('output')
        self.wait_time = kwargs.get('wait_time') or 2
        proxy = kwargs.get('proxy') or PROXY
        self.proxy = {
            'http': proxy,
            'https': proxy,
        }

    def save_file(self, dump_id):
        dump_file = '{}/{}.txt'.format(
            self.output_path, dump_id
        )
        if os.path.exists(dump_file):
            return
        base_url = self.base_url.format(dump_id)
        time.sleep(self.wait_time)
        response = requests.get(base_url, proxies=self.proxy)
        if not response.status_code == 200:
            print(f'Data for {dump_id} does not exist!!')
            return
        html_response = fromstring(response.content)
        plain_text = get_text(html_response)
        with open(dump_file, 'w') as f:
            f.write(plain_text)
        print('{} done..!'.format(dump_file))

    def do_scrape(self):
        print('************  JustPasteIt Scrapper Started  ************\n')
        print('Generating keywords...')
        keywords = get_keywords()
        print(f'Keywords generated. Total keywords: {len(keywords)}')
        for dump_id in keywords:
            self.save_file(dump_id)


def main():
    template = JustPasteItScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

import re
import os
import datetime
import requests
import time
import traceback
from lxml.html import fromstring


class PasteBinScrapper:
    def __init__(self, kwargs):
        self.api_url = 'https://psbdmp.ws/api/dump/get/timeval/{}/{}'
        self.dump_url = 'https://pastebin.com/{}'
        self.start_date = kwargs.get('topic_start')
        self.end_date = kwargs.get('topic_end')
        self.output_path = kwargs.get('output')

    def get_ts(self, date_string):
        try:
            pattern = '%Y/%m/%d'
            ts = int(datetime.datetime.strptime(
                date_string, pattern).timestamp())
            return ts
        except:
            return

    def save_file(self, _id):
        dump_file = '{}/{}.txt'.format(
            self.output_path, _id
        )
        if os.path.exists(dump_file):
            return
        dump_url = self.dump_url.format(_id)
        content = requests.get(dump_url).content
        if not content:
            return
        html_response = fromstring(content)
        raw_text = html_response.xpath(
            '//textarea[@class="paste_code"]/text()'
        )
        if not raw_text:
            return
        with open(dump_file, 'w') as f:
            f.write(raw_text[0])
        print('{} done..!'.format(dump_file))

    def do_scrape(self):
        print('************  Pastebin Scrapper Started  ************\n')
        start_ts = self.get_ts(self.start_date)
        end_ts = self.get_ts(self.end_date)
        if not start_ts:
            print('Invalid format for start date')
            return
        if not end_ts:
            print('Invalid format for end date')
            return
        try:
            url = self.api_url.format(start_ts, end_ts)
            response = requests.get(url).json()
            for data in response['data']:
                self.save_file(data['id'])
        except:
            traceback.print_exc()
            pass


def main():
    template = PasteBinScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

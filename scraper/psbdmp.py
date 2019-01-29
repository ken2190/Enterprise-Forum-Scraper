import re
import os
import datetime
from requests import Session
import time
import traceback
from lxml.html import fromstring


class PasteBinScrapper:
    def __init__(self, kwargs):
        self.api_url = 'https://psbdmp.ws/api/dump/get/timeval/{}/{}'
        self.dump_url = 'https://pastebin.com/{}'
        self.start_date = "2015/01/01"
        self.output_path = kwargs.get('output')
        self.session = Session()
        if kwargs.get('proxy'):
            self.session.proxies = {
                'http': kwargs.get('proxy'),
                'https': kwargs.get('proxy'),
            }

    def get_ts(self,):
        try:
            pattern = '%Y/%m/%d'
            start_date = datetime.datetime.strptime(self.start_date, pattern)
            start_ts = int(start_date.timestamp())
            end_date = start_date + datetime.timedelta(days=7)
            end_ts = int(end_date.timestamp())
            if end_ts > int(datetime.datetime.now().timestamp()):
                return
            self.start_date = end_date.strftime(pattern)
            print('\n\nStart date: {}, End date: {}'
                  .format(start_date, end_date))
            return start_ts, end_ts
        except:
            traceback.print_exc()
            return

    def save_file(self, _id):
        dump_file = '{}/{}.txt'.format(
            self.output_path, _id
        )
        if os.path.exists(dump_file):
            return
        dump_url = self.dump_url.format(_id)
        content = self.session.get(dump_url).content
        if not content:
            return
        html_response = fromstring(content)
        raw_text = html_response.xpath(
            '//textarea[@class="paste_code"]/text()'
        )
        if not raw_text:
            print('IP banned')
            return
        with open(dump_file, 'w') as f:
            f.write(raw_text[0])
        print('{} done..!'.format(dump_file))

    def do_scrape(self):
        print('************  Pastebin Scrapper Started  ************\n')
        while True:
            ts = self.get_ts()
            if not ts:
                return
            start_ts, end_ts = ts
            try:
                url = self.api_url.format(start_ts, end_ts)
                response = self.session.get(url).json()
                if response.get('error_info'):
                    print(response['error_info'])
                    continue
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

import re
import os
import datetime
import requests
import time
import traceback
from lxml.html import fromstring


class PasteBinScrapper:
    def __init__(self, kwargs):
        self.base_url = 'https://psbdmp.ws'
        self.daily_url = self.base_url + '/daily'
        self.dump_url = 'https://psbdmp.ws/api/dump/get/{}'
        self.output_path = kwargs.get('output')

    def save_file(self, dump_id, output_path):
        dump_file = '{}/{}.txt'.format(
            output_path, dump_id
        )
        if os.path.exists(dump_file):
            return
        dump_url = self.dump_url.format(dump_id)
        response = requests.get(dump_url).json()
        if not response:
            return
        if response.get('error_info'):
            print(response['error_info'])
            return
        with open(dump_file, 'w') as f:
            f.write(response['data'])
        print('{} done..!'.format(dump_file))

    def do_scrape(self):
        print('************  Pastebin Scrapper Started  ************\n')
        content = requests.get(self.daily_url).content
        html_response = fromstring(content)
        daily_dumps = html_response.xpath(
            '//div[@class="container"]/table//td')
        for daily_dump in reversed(daily_dumps):
            try:
                url = daily_dump.xpath('a/@href')
                date = daily_dump.xpath('a/text()')
                if not url:
                    continue
                output_path = '{}/{}'.format(self.output_path, date[0])
                if os.path.exists(output_path):
                    continue
                os.makedirs(output_path)
                print('\nGetting dump for {}'.format(date[0]))
                print('--------------------------------')
                url = self.base_url + url[0]
                content = requests.get(url).content
                html_response = fromstring(content)
                dump_ids = html_response.xpath(
                    '//div[@class="container"]/table//td/a')
                for dump_id in dump_ids:
                    dump_id = dump_id.xpath('text()')[0]
                    self.save_file(dump_id, output_path)
            except:
                traceback.print_exc()
                pass


def main():
    template = PasteBinScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

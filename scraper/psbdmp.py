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
        self.start_url = 'https://psbdmp.ws/api/dump/getbydate'
        self.dump_url = 'https://psbdmp.ws/archive/{}'
        self.output_path = kwargs.get('output')
        self.date_format = '%d.%m.%Y'
        self.start_date = datetime.datetime.strptime(kwargs.get('start_date'), self.date_format)

    def save_file(self, dump_id, output_path):
        dump_file = '{}/{}.txt'.format(
            output_path, dump_id
        )
        if os.path.exists(dump_file):
            print('{} already exists..!'.format(dump_file))
            return
        dump_url = self.dump_url.format(dump_id)
        response = requests.get(dump_url).text
        html_response = fromstring(response)
        content = html_response.xpath(
            '//div[@class="content article-body"]/descendant::text()')
        content = ''.join(content)
        with open(dump_file, 'w') as f:
            f.write(content)
        print('{} done..!'.format(dump_file))

    def do_scrape(self):
        print('************  Pastebin Scrapper Started  ************\n')
        while self.start_date < datetime.datetime.now():
            try:
                _from = self.start_date.strftime(self.date_format)
                output_path = '{}/{}'.format(self.output_path, _from)
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                self.start_date = self.start_date + datetime.timedelta(days=1)
                _to = self.start_date.strftime(self.date_format)
                data = {
                    'from': _from,
                    'to': _to
                }
                print('\nGetting dump for {}'.format(_from))
                response = requests.post(self.start_url, data=data)
                json_data = response.json()
                for data in json_data['data']:
                    dump_id = data['id']
                    self.save_file(dump_id, output_path)
            except:
                traceback.print_exc()
                pass


def main():
    template = PasteBinScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()

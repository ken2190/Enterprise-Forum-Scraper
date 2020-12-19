import json
import re
import os
import datetime
import time
import scrapy
import traceback
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scraper.base_scrapper import PROXY_USERNAME, PROXY_PASSWORD, PROXY

REQUEST_DELAY = 0.5
NO_OF_THREADS = 5
API_KEY = 'b15b2a61fe195e6b1cedab735cd13674'


class PsbdmpSpider(SitemapSpider):
    name = 'psbdmp_spider'
    base_url = 'https://psbdmp.ws'
    start_url = 'https://psbdmp.ws/api/v3/getbydate'
    dump_url = f'https://psbdmp.ws/api/v3/dump/{{}}?key={API_KEY}'

    # Other settings
    use_proxy = True
    date_format = '%Y-%m-%d'
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS

    def start_requests(self,):
        while self.start_date < datetime.datetime.now():
            _from = self.start_date.strftime(self.date_format)
            self.start_date = self.start_date + datetime.timedelta(days=1)
            _to = self.start_date.strftime(self.date_format)
            formdata = {
                'from': _from,
                'to': _to
            }
            output_path = '{}/{}'.format(self.output_path, _from)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            yield scrapy.FormRequest(
                self.start_url,
                formdata=formdata,
                dont_filter=True,
                method='POST',
                meta={'output_path': output_path}
            )

    def parse(self, response):
        json_data = json.loads(response.text)
        for data in json_data[0]:
            dump_id = data['id']
            dump_url = self.dump_url.format(dump_id)
            yield scrapy.Request(
                dump_url,
                callback=self.save_file,
                meta={
                    'dump_id': dump_id,
                    'output_path': response.meta['output_path']
                }
            )

    def save_file(self, response):
        output_path = response.meta['output_path']
        dump_id = response.meta['dump_id']
        dump_file = '{}/{}.txt'.format(
            output_path, dump_id
        )
        if os.path.exists(dump_file):
            print('{} already exists..!'.format(dump_file))
            return

        content = response.text
        if not content:
            return
        with open(dump_file, 'w') as f:
            f.write(content)
        print('{} done..!'.format(dump_file))


class PsbdmpScrapper(SiteMapScrapper):
    spider_class = PsbdmpSpider
    site_name = 'psbdmp.ws'
    site_type = 'paste'

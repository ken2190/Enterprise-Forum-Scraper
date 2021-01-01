import json
import re
import os
from os import listdir
from os.path import isfile, join

import datetime
import time
import scrapy
import traceback
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scraper.base_scrapper import PROXY_USERNAME, PROXY_PASSWORD, PROXY

MIN_DELAY=0.4
MAX_DELAY=0.5
API_KEY = 'b15b2a61fe195e6b1cedab735cd13674'
NO_OF_THREADS = 12

class PsbdmpSpider(SitemapSpider):
    name = 'psbdmp_spider'
    base_url = 'https://psbdmp.ws'
    start_url = 'https://psbdmp.ws/api/v3/getbydate'
    dump_url = f'https://psbdmp.ws/api/v3/dump/{{}}?key={API_KEY}'

    # Other settings
    use_proxy = True
    download_thread = NO_OF_THREADS
    
    date_format = '%Y-%m-%d'

    def start_requests(self,):
        if not self.end_date:
            self.end_date = datetime.datetime.now()
        while self.start_date < self.end_date:
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
        data = json_data[0]
        output_path = response.meta['output_path']

        onlyfiles = [f.split(".")[0] for f in listdir(output_path) if isfile(join(output_path, f))]
        for data in json_data[0]:
            dump_id = data['id']
            dump_url = self.dump_url.format(dump_id)
            if dump_id not in onlyfiles:
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

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings

import re
import os
import glob
from lxml.html import fromstring
folder_path = '/Users/PathakUmesh/Downloads/kickass_to_rename'

for file in glob.glob(folder_path+'/*'):
    if os.path.isfile(file):
        file_name_only = file.rsplit('/', 1)[-1].replace('.html', '')
        if not re.findall(r'(.*[a-zA-z]+)', file_name_only):
            continue
        with open(file, 'rb') as f:
            response = fromstring(f.read())
            topic_id = response.xpath(
                '//a[@class="button new_reply_button" or '
                '@class="button closed_button"]/@href')
            if topic_id:
                topic_id = re.findall(r'tid=(\d+)', topic_id[0])
                pagination = response.xpath(
                    '//span[@class="pagination_current"]/text()'
                    )
                pagination = pagination[0] if pagination else 1
                new_name = f'{topic_id[0]}-{pagination}.html'
                to_rename = f'{folder_path}/{new_name}'
                if os.path.exists(new_name):
                    continue
                # print(to_rename)
                os.rename(file, to_rename)
                print('Renamed "{}" to "{}"'.format(file, to_rename))
                continue
            user_id = response.xpath(
                '//a[text()="Find All Posts"]/@href')
            if user_id:
                user_id = re.findall(r'uid=(\d+)', user_id[0])
                if not user_id:
                    continue
                new_name = f'UID-{user_id[0]}.html'
                to_rename = f'{folder_path}/{new_name}'
                if os.path.exists(new_name):
                    continue
                # print(to_rename)
                os.rename(file, to_rename)
                print('Renamed "{}" to "{}"'.format(file, to_rename))
                continue
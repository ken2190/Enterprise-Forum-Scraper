import re
import os
import glob
folder_path = '/Users/PathakUmesh/Desktop/Cracked'

for file in glob.glob(folder_path+'/*'):
    if os.path.isfile(file):
        # print(file)
        topic= file.rsplit('/', 1)[-1].split('--')[0]
        topic_id = str(
            int.from_bytes(
                topic.encode('utf-8'), byteorder='big'
            ) % (10 ** 7)
        )
        # print(topic_id)
        match = re.findall(r'--(\d+)', file)
        pagination = match[0] if match else 1
        # print(pagination)
        to_rename = '{}/{}-{}.html'.format(folder_path, topic_id, pagination)
        # print(to_rename)
        os.rename(file, to_rename)
        print('Renamed "{}" to "{}"'.format(file, to_rename))

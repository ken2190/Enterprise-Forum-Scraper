import re
import os
import glob
folder_path = '/Users/PathakUmesh/Programming_stuffs/DataViper/files_to_rename'


for file in glob.glob(folder_path+'/*'):
    if os.path.isfile(file):
        # print(file)
        file_name_only = file.rsplit('/', 1)[-1].split('.html')[0]
        topic_id = str(
            int.from_bytes(
                file_name_only.encode('utf-8'), byteorder='big'
            ) % (10 ** 7)
        )
        # print(topic_id)
        match = re.findall(r'-(\d+)\.html', file)
        pagination = match[0] if match else 1
        # print(pagination)
        to_rename = '{}/{}-{}.html'.format(folder_path, topic_id, pagination)
        # print(to_rename)
        os.rename(file, to_rename)
        print('Renamed "{}" to "{}"'.format(file, to_rename))

# path = '/Users/PathakUmesh/Programming_stuffs/DataViper/merge csv/filenames.txt'
# with open(path, 'r') as f:
#     for line in f.readlines():
#         file_name = '{}/{}'.format(folder_path, line.strip())
#         with open(file_name, 'w') as f:
#             pass

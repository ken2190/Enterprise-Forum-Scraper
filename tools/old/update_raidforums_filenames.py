import re
import os
import glob
folder_path = '/Users/PathakUmesh/Programming_stuffs/DataViper/files_to_rename'


base_url = "https://raidforums.com/Thread-"
for file in glob.glob(folder_path+'/*'):
    if os.path.isfile(file):
        # print(file)
        file_name_only = file.rsplit('/', 1)[-1].split('?page')[0]
        link = '{}{}'.format(base_url, file_name_only)
        # print(link)
        topic_id = str(
            int.from_bytes(
                link.encode('utf-8'), byteorder='big'
            ) % (10 ** 7)
        )
        # print(topic_id)
        match = re.findall(r'page=(\d+)', file)
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
#         link = '{}{}'.format(base_url, line.strip())
#         print(link)

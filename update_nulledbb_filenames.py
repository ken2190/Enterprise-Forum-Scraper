import re
import os
import glob
folder_path = '/Users/PathakUmesh/Programming_stuffs/DataViper/files_to_rename'

def update_names():
    for file in glob.glob(folder_path+'/*'):
        if os.path.isfile(file):
            match = re.findall(r'.*/(.*)-\d+\.html', file)
            if not match:
                continue
            topic_id = str(
                int.from_bytes(
                    match[0].encode('utf-8'), byteorder='big'
                ) % (10 ** 7)
            )
            # print(topic_id)
            match = re.findall(r'-(\d+)\.html', file)
            pagination = match[0] if match else 1
            file_to_rename = '{}-{}.html'.format(topic_id, pagination)
            path_to_rename = '{}/{}'.format(folder_path, file_to_rename)
            # print(to_rename)
            os.rename(file, path_to_rename)
            print('Renamed "{}" to "{}"'.format(file.rsplit('/', 1)[-1], file_to_rename))


def create_test_files():
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    path = '/Users/PathakUmesh/Programming_stuffs/DataViper/files_to_rename/filenames.txt'
    names = """zHitman-Leak-1.html
    zHitman-The-unique-Hitman-System-with-an-in-game-1-0-3-1.html
    Zihua-Sunset-1.html
    Zin-1.html
    Zin-s-BTC-Exchange-Service-Get-BTC-in-exchange-for-PayPal-10-2.html
    Zin-s-BTC-Exchange-Service-Get-BTC-in-exchange-for-PayPal-10-3.html
    Zircon-II-%E2%80%93-Creativemarket-Drupal-Theme-1.html
    ZmLab-drugs-meth--127261-1.html
    Zoe-1.html
    Zoe-2.html
    Zoe-3.html
    ZolticMC-Network-1-7-1-8-2.html
    Zombie-Avatar-1.html
    Zombie-Escape-1.html
    Zombie-Hunter-1.html
    zombie-mod-1.html
    ZombieRP-Still-a-thing-1.html
    Zombies-1.html
    Zombies-2.html
    Zombies-BO4-1.html
    Zombies-good-or-naw-1.html
    Zombies-is-my-salvation-1.html
    Zombies-Minigame-v-0-8-5-triipoloski-1.html
    Zombies-Tower-Defense-1-7-1.html
    Zoomie-Social-Media-Mobile-App-1.html
    zoominfo-checker-account-Needed-1.html
    zotiyac-1.html
    Zox-News-Professional-WordPress-News-Magazine-Theme-3-1-0-1.html"""
    for line in names.split('\n'):
        file_name = '{}/{}'.format(folder_path, line.strip())
        with open(file_name, 'w') as f:
            pass

if __name__ == '__main__':
    # create_test_files()
    update_names()
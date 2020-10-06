#!/usr/bin/env python3

"""
An import service tool
"""

import os
import shutil
import subprocess
import sys


IMPORT_DIR = r"/data/processing/forums/import/"
BACKUP_DIR = r"/data/processing/forums/backup/"


def copy_folder_files(src_folder, dst_folder):
    for filename in os.listdir(src_folder):
        src_file = os.path.join(src_folder, filename)
        dst_file = os.path.join(dst_folder, filename)

        shutil.copy(src_file, dst_file)


def clean_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def main():
    # execute RSYNC command to get files from scraping server
    print('Executing RSYNC...')
    cmd = "rsync -avz -e 'ssh -i ~/.ssh/proxima.pem' root@51.161.115.138:/data/processing/import/* /data/processing/forums/import/"
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=True
        )
    except subprocess.CalledProcessError as err:
        print(
            "ERROR: rsync failed: retcode=%d, "
            "err=%s" % (err.returncode, err.stderr.decode('utf-8'))
        )
        sys.exit(2)

    # make a copy of imported files to backup folder
    print("Making a copy of imported files to backup folder...")
    try:
        copy_folder_files(IMPORT_DIR, BACKUP_DIR)
    except Exception as err:
        print(
            "ERROR: backup failed: %s" % err
        )
        sys.exit(2)

    # Import to elastic
    print("Importing to Elastic...")
    cmd = "elasticdump --input={} --output=http://localhost:9200/dv-f001 --noRefresh --limit=10000".split()
    log_file = "/var/log/elasticimport.log"

    with open(log_file, 'a') as f:
        for filename in os.listdir(IMPORT_DIR):
            f.write(filename + '\n')
            filepath = os.path.join(IMPORT_DIR, filename)
            cmd[1] = cmd[1].format(filepath)
            try:
                subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    check=True
                )
            except subprocess.CalledProcessError as err:
                print(
                    "ERROR: elasticdump failed: retcode=%d, "
                    "err=%s" % (err.returncode, err.stderr.decode('utf-8'))
                )
                sys.exit(2)

    # remove import folder
    print("Cleaning import folder...")
    clean_folder(IMPORT_DIR)
    print("Done")


if __name__ == '__main__':
    main()

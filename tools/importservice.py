#!/usr/bin/env python3

"""
An import service tool
"""

import os
import shutil
import subprocess
import sys


IMPORT_DIR = "/data/processing/forums/import/"
BACKUP_DIR = "/data/processing/forums/backup/"


def copy_folder_files(src_folder, dst_folder):
    """
    Copies all non-empty files from the src_folder to dst_folder.
    Removes empty files.
    """

    for filename in os.listdir(src_folder):
        src_file = os.path.join(src_folder, filename)
        dst_file = os.path.join(dst_folder, filename)

        if os.path.isfile(src_file):
            if os.path.getsize(src_file) == 0:
                os.unlink(src_file)
            else:
                shutil.copy(src_file, dst_file)


def clean_folder(folder):
    """ Removes folder contents """

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
    # create IMPORT_DIR if not exists
    if not os.path.exists(IMPORT_DIR):
        print(f'Creating folder {IMPORT_DIR}...')
        os.makedirs(IMPORT_DIR)

    # create BACKUP_DIR if not exists
    if not os.path.exists(BACKUP_DIR):
        print(f'Creating folder {BACKUP_DIR}...')
        os.makedirs(BACKUP_DIR)

    # execute RSYNC command to get files from scraping server
    print('Executing RSYNC...')
    cmd = ("rsync -avz -e 'ssh -i ~/.ssh/proxima.pem' root@51.161.115.138:/data/processing/import/*"
           " /data/processing/forums/import/")
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

    with open(log_file, 'a', encoding='utf-8') as f:
        for filename in os.listdir(IMPORT_DIR):
            print(f'  File {filename}...')
            f.write('File: ' + filename + '\n')
            filepath = os.path.join(IMPORT_DIR, filename)
            current_cmd = cmd.copy()
            current_cmd[1] = current_cmd[1].format(filepath)
            try:
                command_line_process = subprocess.run(
                    current_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True
                )
            except subprocess.CalledProcessError as err:
                print(
                    "ERROR: elasticdump failed: retcode=%d, "
                    "err=%s" % (err.returncode, err.stdout.decode('utf-8'))
                )
                sys.exit(2)
            else:
                f.write(command_line_process.stdout.decode('utf-8') + '\n')

    # remove the files from the remote server
    print("Removing the files from the remote server...")
    for filename in os.listdir(IMPORT_DIR):
        filepath = os.path.join(IMPORT_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        print(f'  File {filename}...')
        cmd = (f"ssh -i ~/.ssh/proxima.pem root@51.161.115.138 "
               f"'rm -f /data/processing/import/{filename}'")
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
                "ERROR: failed to remove file %s, retcode=%d, "
                "err=%s" % (filename, err.returncode, err.stderr.decode('utf-8'))
            )
            sys.exit(2)
        else:
            os.unlink(filepath)

    # remove import folder
    print("Cleaning import folder...")
    clean_folder(IMPORT_DIR)
    print("Done")


if __name__ == '__main__':
    main()

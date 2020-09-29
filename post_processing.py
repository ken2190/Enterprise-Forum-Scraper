#!/usr/bin/env python3

"""
Post processing utility
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile

from settings import (
    OUTPUT_DIR,
    PARSE_DIR,
    COMBO_DIR,
    ARCHIVE_DIR,
    IMPORT_DIR,
    OFFSITE_DEST
)


def parse_args():
    """ Parses cmdline arguments """

    parser = argparse.ArgumentParser(description='Post processing utility')
    parser.add_argument('-site', help='A site name', required=True)
    parser.add_argument('-date', help='A datestamp', required=True)
    parser.add_argument('--sync', help='Sync with cloud', action='store_true',
                        default=False)

    args, _ = parser.parse_known_args()
    return args


def check_input_dirs(html_dir, parse_dir):
    """ Checks input data """

    def is_dir_exists(path):
        return os.path.exists(path) and os.path.isdir(path)

    if not is_dir_exists(html_dir):
        print("ERROR STAGE 0: Scraper output directory does not exist: %s"
              % html_dir)
        sys.exit(2)

    if not is_dir_exists(parse_dir):
        print("ERROR STAGE 0: Parsing output directory does not exist: %s"
              % PARSE_DIR)
        sys.exit(2)

    if not is_dir_exists(COMBO_DIR):
        print("WARNING: JSON combo directory does not exist: %s" % COMBO_DIR)
        os.makedirs(COMBO_DIR)

    arch_original_dir = os.path.join(ARCHIVE_DIR, 'original')
    if not is_dir_exists(arch_original_dir):
        print("WARNING: Archive directory does not exist: %s" % ARCHIVE_DIR)
        os.makedirs(arch_original_dir)

    if not is_dir_exists(IMPORT_DIR):
        print("ERROR: Import directory does not exist: %s" % IMPORT_DIR)
        sys.exit(2)


def make_tarfile(output_filename, source):
    """ Creates a .tar.gz archive """

    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source)

    if os.path.isdir(source):
        for f in os.listdir(source):
            print(os.path.join(source, f))
    else:
        print(source)


def run():
    """ Main program flow """

    # parse cmdline arguments
    args = parse_args()

    # prepare paths
    html_dir = os.path.join(OUTPUT_DIR, args.site)
    parse_dir = os.path.join(PARSE_DIR, args.site)

    # check input dirs
    print('Checking paths...')
    check_input_dirs(html_dir, parse_dir)

    # check if the parse dir contain at least one file
    if not os.listdir(parse_dir):
        print(f"{parse_dir} is Empty")

    ##############################################
    # merge parsed files
    ##############################################
    print('Combining JSON files...')
    cmd = f"jq -c '.' {parse_dir}/*.json"
    combined_json_file = os.path.join(
        COMBO_DIR,
        f'{args.site}-{args.date}.json'
    )
    try:
        with open(combined_json_file, 'a') as f:
            subprocess.run(
                cmd,
                cwd=parse_dir,
                check=True,
                shell=True,
                stdout=f,
                stderr=subprocess.PIPE
            )
    except subprocess.CalledProcessError as err:
        print(
            "ERROR: JQ exited with non-zero exit code: retcode=%d, err=%s" %
            (err.returncode, err.stderr)
        )
        sys.exit(2)

    ##############################################
    # archive scraped HTML and combined JSON
    ##############################################
    print('Archiving HTML files...')
    html_archive = os.path.join(
        ARCHIVE_DIR,
        'original',
        f'{args.site}-html-{args.date}.tar.gz'
    )
    try:
        make_tarfile(html_archive, html_dir)
    except OSError as err:
        print("ERROR: Failed to create HTML archive: %s" % err)
        sys.exit(2)

    print('Archiving the combined JSON file...')
    combined_json_archive = os.path.join(
        ARCHIVE_DIR,
        f'{args.site}-{args.date}.tar.gz'
    )
    try:
        make_tarfile(combined_json_archive, combined_json_file)
    except OSError as err:
        print("ERROR: Failed to create JSON archive: %s" % err)
        sys.exit(2)

    ##############################################
    # move combined JSON to import dir
    ##############################################
    print('Moving the combined JSON file to import folder...')
    try:
        shutil.move(combined_json_file, IMPORT_DIR)
    except OSError as err:
        print("ERROR: Failed to move JSON to import directory: %s" % err)
        sys.exit(2)

    ##############################################
    # delete scraped HTML and parsed JSON files
    ##############################################
    print('Deleting source HTML and JSON files...')
    if not os.path.exists(html_archive):
        print("ERROR: missing archive file %s" % html_archive)
        sys.exit(2)
    elif os.path.getsize(html_archive) == 0:
        print("ERROR: empty archive file %s" % html_archive)
        sys.exit(2)
    else:
        shutil.rmtree(html_dir)
        shutil.rmtree(parse_dir)

    ##############################################
    # send archives offset
    ##############################################
    if args.sync:
        print('Running rclone tool...')
        try:
            result = subprocess.run(
                ["rclone", "copy", ARCHIVE_DIR, OFFSITE_DEST, "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as err:
            print(
                "ERROR: Failed to copy archive directory offset: retcode=%d, "
                "err=%s" % (err.returncode, err.stderr)
            )
            sys.exit(2)

    print('Done')


if __name__ == '__main__':
    run()

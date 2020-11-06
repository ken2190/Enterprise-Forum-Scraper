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

from scraper import SCRAPER_MAP


def parse_args():
    """ Parses cmdline arguments """

    parser = argparse.ArgumentParser(description='Post processing utility')
    parser.add_argument('-site', help='A site name', required=True)
    parser.add_argument('-date', help='A datestamp', required=True)
    parser.add_argument('--sync', help='Sync with cloud', action='store_true',
                        default=False)

    args, _ = parser.parse_known_args()
    return args


def check_input_dirs(html_dir, parse_dir, site_type, exit):
    """ Checks input data """

    def is_dir_exists(path):
        return os.path.exists(path) and os.path.isdir(path)

    if not is_dir_exists(html_dir):
        err_msg = "ERROR STAGE 0: Scraper output directory does not exist: %s" % html_dir
        print(err_msg)
        exit(2, RuntimeError(err_msg))

    if not is_dir_exists(parse_dir):
        err_msg = "ERROR STAGE 0: Parsing output directory does not exist: %s" % PARSE_DIR
        print(err_msg)
        exit(2, RuntimeError(err_msg))

    if not is_dir_exists(COMBO_DIR):
        print("WARNING: JSON combo directory does not exist: %s" % COMBO_DIR)
        os.makedirs(COMBO_DIR)

    arch_original_dir = os.path.join(ARCHIVE_DIR, site_type, 'original')
    if not is_dir_exists(arch_original_dir):
        print("WARNING: Archive directory does not exist: %s" % ARCHIVE_DIR)
        os.makedirs(arch_original_dir)

    import_dir = os.path.join(IMPORT_DIR, site_type)
    if not is_dir_exists(import_dir):
        err_msg = "ERROR: Import directory does not exist: %s" % import_dir
        print(err_msg)
        exit(2, RuntimeError(err_msg))


def make_tarfile(output_filename, source):
    """ Creates a .tar.gz archive """

    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source)

    if os.path.isdir(source):
        for f in os.listdir(source):
            print(os.path.join(source, f))
    else:
        print(source)


def run(kwargs=None):
    """ Main program flow """

    if kwargs:
        args = None
        site = kwargs['site']
        date = kwargs['date']
        sync = kwargs.get('sync', False)
    else:
        # parse cmdline arguments
        args = parse_args()
        site = args.site
        date = args.date
        sync = args.sync

    def exit(exit_code=2, exception=None):
        if args:
            sys.exit(exit_code)
        else:
            raise exception

    # prepare paths
    html_dir = os.path.join(OUTPUT_DIR, site)
    parse_dir = os.path.join(PARSE_DIR, site)

    scraper = SCRAPER_MAP.get(site)
    if not scraper:
        err_msg = "ERROR: Invalid site name"
        print(err_msg)
        exit(2, RuntimeError(err_msg))

    site_type = getattr(scraper, 'site_type', None)
    if not site_type:
        err_msg = f"ERROR: {site} has no site_type set"
        print(err_msg)
        exit(2, RuntimeError(err_msg))
    # check input dirs
    print('Checking paths...')
    check_input_dirs(html_dir, parse_dir, site_type, exit)

    # check if the parse dir contain at least one file
    if not os.listdir(parse_dir):
        err_msg = f"{parse_dir} is Empty"
        print(err_msg)
        exit(2, RuntimeError(err_msg))

    ##############################################
    # merge parsed files
    ##############################################
    print('Combining JSON files...')
    cmd = f"jq -c '.' {parse_dir}/*.json"
    combined_json_file = os.path.join(
        COMBO_DIR,
        f'{site}-{date}.json'
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
        exit(2, err)

    ##############################################
    # archive scraped HTML and combined JSON
    ##############################################
    print('Archiving HTML files...')
    html_archive = os.path.join(
        ARCHIVE_DIR,
        site_type,
        'original',
        f'{site}-html-{date}.tar.gz'
    )
    try:
        make_tarfile(html_archive, html_dir)
    except OSError as err:
        print("ERROR: Failed to create HTML archive: %s" % err)
        exit(2, err)

    print('Archiving the combined JSON file...')
    combined_json_archive = os.path.join(
        ARCHIVE_DIR,
        site_type,
        f'{site}-{date}.tar.gz'
    )
    try:
        make_tarfile(combined_json_archive, combined_json_file)
    except OSError as err:
        print("ERROR: Failed to create JSON archive: %s" % err)
        exit(2, err)

    ##############################################
    # move combined JSON to import dir
    ##############################################
    print('Moving the combined JSON file to import folder...')
    import_dir = os.path.join(IMPORT_DIR, site_type)
    try:
        shutil.move(combined_json_file, import_dir)
    except OSError as err:
        print("ERROR: Failed to move JSON to import directory: %s" % err)
        exit(2, err)

    ##############################################
    # delete scraped HTML and parsed JSON files
    ##############################################
    print('Deleting source HTML and JSON files...')
    if not os.path.exists(html_archive):
        print("ERROR: missing archive file %s" % html_archive)
        exit(2, err)
    elif os.path.getsize(html_archive) == 0:
        print("ERROR: empty archive file %s" % html_archive)
        exit(2, err)
    else:
        shutil.rmtree(html_dir)
        shutil.rmtree(parse_dir)

    ##############################################
    # send archives offset
    ##############################################
    if sync:
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
            exit(2, err)

    print('Done')


if __name__ == '__main__':
    run()

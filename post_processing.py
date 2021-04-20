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
    parser.add_argument('-template', help='Template name for this site', required=True)
    parser.add_argument('-date', help='A datestamp', required=True)
    parser.add_argument('--sync', help='Sync with cloud', action='store_true',
                        default=False)

    args, _ = parser.parse_known_args()
    return args


def check_input_dirs(html_dir, parse_dir, site_type):
    """ Checks input data """

    def is_dir_exists(path):
        return os.path.exists(path) and os.path.isdir(path)

    if not is_dir_exists(html_dir):
        print_erorr_message_and_raise_exception(
            "ERROR STAGE 0: Scraper output directory does not exist: %s" % html_dir)

    if not is_dir_exists(parse_dir):
        print_erorr_message_and_raise_exception(
            "ERROR STAGE 0: Parsing output directory does not exist: %s" % PARSE_DIR)

    if not is_dir_exists(COMBO_DIR):
        print("WARNING: JSON combo directory does not exist: %s" % COMBO_DIR)
        os.makedirs(COMBO_DIR)

    arch_original_dir = os.path.join(ARCHIVE_DIR, site_type, 'original')
    if not is_dir_exists(arch_original_dir):
        print("WARNING: Archive directory does not exist: %s" % ARCHIVE_DIR)
        os.makedirs(arch_original_dir)

    import_dir = os.path.join(IMPORT_DIR, site_type)
    if not is_dir_exists(import_dir):
        warning_message = "Warning: Import directory does not exist: %s" % import_dir
        os.makedirs(import_dir)
        print(warning_message)


def make_tarfile(output_filename, source):
    """ Creates a .tar.gz archive """

    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source)

    if os.path.isdir(source):
        for f in os.listdir(source):
            print(os.path.join(source, f))
    else:
        print(source)


def exit_func(exit_code=2, exception=None):
    if not exception:
        sys.exit(exit_code)
    else:
        raise exception


def validate_output_json_file(combined_json_file):
    validate_output_file("output_json", combined_json_file)


def validate_json_archive_file(combined_json_archive):
    validate_output_file("json_archive", combined_json_archive)


def validate_output_file(file_label, output_file_name):
    if not os.path.exists(output_file_name):
        print_erorr_message_and_raise_exception(
            f"ERROR: cannot find the {file_label} file at ({output_file_name}). Aborting.")
    if os.path.getsize(output_file_name) == 0:
        print_erorr_message_and_raise_exception(
            f"ERROR:  The {file_label} file at ({output_file_name}) is empty. Aborting.")


def print_erorr_message_and_raise_exception(error_message):
    print(error_message)
    exit_func(2, RuntimeError(error_message))


def run(kwargs=None):
    """ Main program flow """

    if kwargs:
        args = None
        site = kwargs['site']
        template = kwargs['template']
        date = kwargs['date']
        sync = kwargs.get('sync', False)
    else:
        # parse cmdline arguments
        args = parse_args()
        site = args.site
        template = args.template
        date = args.date
        sync = args.sync

    scraper = SCRAPER_MAP.get(template)
    if not scraper:
        err_msg = "ERROR: Invalid site template"
        print(err_msg)
        exit_func(2, RuntimeError(err_msg))

    site_type = getattr(scraper, 'site_type', None)
    if not site_type:
        err_msg = f"ERROR: {site} has no site_type set"
        print(err_msg)
        exit_func(2, RuntimeError(err_msg))

    # prepare paths
    if site_type == 'shadownet':
        html_dir = os.path.join(OUTPUT_DIR, site_type, site)
        parse_dir = os.path.join(PARSE_DIR, site_type, site)
    else:
        html_dir = os.path.join(OUTPUT_DIR, site)
        parse_dir = os.path.join(PARSE_DIR, site)

    # check input dirs
    print('Checking paths...')
    check_input_dirs(html_dir, parse_dir, site_type)

    # check if the parse dir contain at least one file
    if not os.listdir(parse_dir):
        err_msg = f"{parse_dir} is Empty"
        print(err_msg)
        exit_func(0)

    ##############################################
    # merge parsed files
    ##############################################
    print('Combining JSON files...')
    cmd = 'find . -name \\*.json -exec cat {} + | jq -c .'
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
        exit_func(2, err)

    validate_output_json_file(combined_json_file)
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
        exit_func(2, err)

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
        exit_func(2, err)

    validate_json_archive_file(combined_json_archive)

    ##############################################
    # move combined JSON to import dir
    ##############################################
    print('Moving the combined JSON file to import folder...')
    import_dir = os.path.join(IMPORT_DIR, site_type)
    try:
        shutil.move(combined_json_file, import_dir)
    except OSError as err:
        print("ERROR: Failed to move JSON to import directory: %s" % err)
        exit_func(2, err)

    ##############################################
    # delete scraped HTML and parsed JSON files
    ##############################################
    print('Deleting source HTML and JSON files...')
    if not os.path.exists(html_archive):
        print_erorr_message_and_raise_exception("ERROR: missing archive file %s" % html_archive)
    elif os.path.getsize(html_archive) == 0:
        print_erorr_message_and_raise_exception("ERROR: empty archive file %s" % html_archive)
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
            exit_func(2, err)
    print('Done')


if __name__ == '__main__':
    run()

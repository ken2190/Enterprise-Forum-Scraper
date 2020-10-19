import re
import os
import sys
import json
from copy import deepcopy

accumulator = []
slash = False

HELP_MESSAGE = """
    Usage: python deduplicate.py --input=path/to/input --output=path/to/output
"""

INPUT_PATH = None
OUTPUT_PATH = None


def write_json(data):
    global slash
    with open(OUTPUT_PATH, 'a+') as op:
        if slash:
            op.write('\n' + json.dumps(data, ensure_ascii=False))
        else:
            op.write(json.dumps(data, ensure_ascii=False))
        slash = True
        print(data)
        print('----------------')


def empty_accumulator():
    global accumulator

    if len(accumulator) == 0:
        return

    img_found = False
    is_different = False
    msg = accumulator[0]['_source']['message']
    prev_author = accumulator[0]['_source']['author']
    winners = []
    for index, data in enumerate(accumulator,0):
        if data['_source']['message'] != msg or data['_source']['author'] != prev_author:
            winners.append(data)
            is_different = True
            continue

        if not img_found and 'img' in data['_source'].keys():
            winners.append(data)
            img_found = True

    if is_different:
        for win in accumulator:
            write_json(win)
        accumulator = []
        return

    if not winners:
        write_json(accumulator[-1])
    else:
        for win in winners:
            write_json(win)

    accumulator = []


def remove_null(data):
    temp = deepcopy(data['_source'])
    for key, value in temp.items():
        if not value:
            data['_source'].pop(key)
    return data


def main():
    with open(INPUT_PATH, 'r') as ip:
        prev_pid = prev_cid = None
        has_cid = True
        for num, line in enumerate(ip, 1):
            try:
                data = json.loads(line)
            except Exception:
                print(f'Invalid json at line: {num}. Ignoring.')
                continue
            data = remove_null(data)
            try:
                cid = data['_source']['cid']
            except Exception:
                if has_cid:
                    empty_accumulator()
                print(f'cid not found in the line: {num}.')
                accumulator.append(data)
                has_cid = False
                continue

            pid = data['_source']['pid']

            if (prev_cid, prev_pid) != (cid, pid):
                empty_accumulator()
            accumulator.append(data)
            prev_cid, prev_pid = cid, pid
            has_cid = True
        empty_accumulator()


for arg in sys.argv[1:]:
    try:
        key = arg.split('=')[0].split('--')[-1]
        value = arg.split('=')[1]
    except:
        print('Missing values.')
        print(HELP_MESSAGE)
        exit()

    if key == 'input':
        # global INPUT_PATH
        INPUT_PATH = value

    if key == 'output':
        # global OUTPUT_PATH
        OUTPUT_PATH = value

if not INPUT_PATH or not OUTPUT_PATH:
    print(HELP_MESSAGE)
    exit()

if os.path.exists(OUTPUT_PATH):
    os.system(f'rm {OUTPUT_PATH}')

if not os.path.exists(INPUT_PATH):
    print("INPUT_PATH doesn't exists.")
    print(HELP_MESSAGE)
    exit()

main()

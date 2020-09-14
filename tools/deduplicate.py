INPUT_PATH = '/Users/mac/programming/filter/data.json'
OUTPUT_PATH = '/Users/mac/programming/filter/result.json'

import json
import re
import os

accumulator = []
slash = False

if os.path.exists(OUTPUT_PATH):
    os.system(f'rm {OUTPUT_PATH}')

def write_json(data):
    global slash
    with open(OUTPUT_PATH, 'a+') as op:
        # print(f'{data["_source"]["cid"]} -cid {data["_source"]["pid"]}-pid done!')        
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
    msg  = accumulator[0]['_source']['message']
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
        write_json(accumulator[0])
    else:
        for win in winners:
            write_json(win)

    accumulator = []


with open(INPUT_PATH, 'r') as ip:
    prev_pid = prev_cid = None
    for num, line in enumerate(ip,1):
        try:
            data = json.loads(line)
        except:
            print(f'Invalid json at line: {num}. Ignoring.')
            continue
        try:
            cid = data['_source']['cid']
        except:
            print(f'cid not found in the line: {num}. Writing anyway.')
            write_json(data)
            continue

        pid = data['_source']['pid']

        if (prev_cid, prev_pid) != (cid, pid):
            empty_accumulator()
        accumulator.append(data)
        prev_cid, prev_pid = cid, pid
    empty_accumulator()


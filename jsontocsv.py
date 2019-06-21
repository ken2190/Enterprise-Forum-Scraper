import re
import csv
import json
import traceback
INTPUT_FILE = 'jsontocsv.txt'
OUTPUT_FILE = 'data.csv'
COLUMNS = [
    'first_name',
    'last_name',
    'email',
    'address',
    'address2',
    'city',
    'state',
    'country',
    'zip',
    'ip_address',
    'phone',
    'carrier'
]

with open(OUTPUT_FILE, 'w') as csvfile:
    csv_writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
    csv_writer.writeheader()
    with open(INTPUT_FILE, 'r') as fp:
        single_json = ''
        for line_number, line in enumerate(fp, 1):
            try:
                if '}' not in line.rstrip('\n'):
                    single_json += line.strip('\n')
                    continue
                each_data = re.sub(r'\s{2,}', '', single_json)
                each_data = each_data.split(',')
                each_data = [
                    i.replace('"', '').strip() for i in each_data
                    if any(col == i.split(':')[0].replace('"', '').strip()
                           for col in COLUMNS)
                ]
                mydict = dict()
                for field in each_data:
                    key, value = [f.strip() for f in field.split(':')]
                    value = re.sub(r'NumberLong\((.*?)\)', '\\1', value)
                    try:
                        if key not in ['phone', 'ip_address'] and int(value):
                            value = ''
                        if key == 'zip' and len(value) > 5 and int(value):
                            value = ''
                    except:
                        pass
                    mydict.update({
                        key.strip(): value.strip()
                    })
                csv_writer.writerow(mydict)
                single_json = ''
            except:
                print('Error in line number:', line_number)
                traceback.print_exc()
                break

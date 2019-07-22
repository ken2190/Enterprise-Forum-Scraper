import re
import csv
import json

INPUT = 'sample1_new.csv'
INPUT_WITH_HASH = 'sample2_new.csv'
OUTPUT = 'merged_output.csv'

hash_map = dict()
with open(INPUT_WITH_HASH, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        hash_map.update({row[0]: row[1]})

with open(INPUT, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    with open(OUTPUT, 'w') as output_csv_file:
        csv_writer = csv.writer(output_csv_file, delimiter=',')
        for index, row in enumerate(csv_reader, 1):
            if row[3] in hash_map:
                row.insert(4, hash_map[row[3]])
            else:
                row.insert(4, None)
            csv_writer.writerow(row)
            print('Writing row {}'.format(index))

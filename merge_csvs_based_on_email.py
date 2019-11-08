import re
import csv
import json

#master file with all data
INPUT = 'masterfile3.csv'

#file with hashes/emails
INPUT_WITH_HASH = 'inputhash.csv'

OUTPUT = 'merged_output3.csv'

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
            if row[0] in hash_map:
                row.insert(1, hash_map[row[0]])
            else:
                row.insert(1, None)
            csv_writer.writerow(row)
            print('Writing row {}'.format(index))

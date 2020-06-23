# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
import dateutil.parser as dparser
#import pandas as pd

USERS = '/Users/PathakUmesh/Downloads/DreamMarket_2017/users.csv'


class BrokenPage(Exception):
    pass


class DreamMarketParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.output_folder = "dream market"
        self.folder_path = folder_path
        # main function
        self.main()

    def main(self):
        # self.process_products()
        self.process_users()

    def process_products(self):
        path = os.path.join(self.folder_path, 'products.csv')
        products_df = pd.read_csv(path)
        output_file = '{}/products.json'.format(str(self.output_folder))
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            for index, row in products_df.iterrows():
                # if index > 50:
                #     break
                row_as_dict = row.to_dict()
                data = {
                    'subject': row_as_dict['product_name'].strip(),
                    'author': row_as_dict['seller_name'].strip(),
                    'message': row_as_dict['description'].strip(),

                }
                if not row_as_dict['sold_since'] == '-':
                    date.update({
                        'date': row_as_dict['sold_since']
                    })
                utils.write_json(file_pointer, data)
                print(f'Row {index} done..!!')

    def process_users(self):
        path = os.path.join(self.folder_path, 'users.csv')
        users_df = pd.read_csv(path)
        output_file = '{}/users.json'.format(str(self.output_folder))
        with open(output_file, 'w', encoding='utf-8') as file_pointer:
            for index, row in users_df.iterrows():
                # if index > 50:
                #     break
                row_as_dict = row.to_dict()
                data = {
                    'author': row_as_dict['seller_name'].strip(),
                    'pgp': row_as_dict['pgp'].strip().replace('BLOCK-----n', 'BLOCK-----\n').replace('n-----END', '\n-----END'),
                }
                utils.write_json(file_pointer, data)
                print(f'Row {index} done..!!')

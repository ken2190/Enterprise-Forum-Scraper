# -- coding: utf-8 --
import json
import os
import re
import traceback
from datetime import datetime

import utils
from .base_template import BaseTemplate


class TelegramParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        self.folder_path = kwargs.get('folder_path')
        self.output_folder = kwargs.get('output_folder')
        self.files = kwargs.get("files")
        self.parser_name = 'telegram'
        self.channel = kwargs.get('sitename')
        self.start_date = kwargs.get("start_date")
        if self.start_date:
            try:
                self.start_date = datetime.strptime(
                    self.start_date,
                    self.time_format
                ).timestamp()
            except:
                pass
        self.main()

    def main(self):
        for file in self.files:
            filename = os.path.basename(file)
            print('----------------------------------------\n')
            print(f"Parsing {file}...")
            output_file_path = os.path.join(self.output_folder, filename)
            try:
                file_pointer = open(output_file_path, 'w', encoding='utf-8')
                self.process_file(
                    file, file_pointer
                )
            except Exception:
                traceback.print_exc()
                continue

    def process_file(self, input_file_path, output_file_pointer):
        with open(input_file_path, 'r') as fp:
            content = fp.read()
            for line in content.split("\n"):
                if line:
                    item = json.loads(line)
                    data = self.process_message(item)
                    if data:
                        utils.write_json(output_file_pointer, data)
        print('\nJson written in {}'.format(output_file_pointer.name))
        print('----------------------------------------\n')

    def process_message(self, msg_object):
        sender = msg_object.get("sender", dict())
        # Init item
        message = msg_object["message"]
        if not message:
            return
        item = {"channel": self.channel, "type": "telegram", "date": msg_object["date"] * 1000,
                "author": sender.get("username", self.channel) if sender else self.channel, "message": message}
        self.populate_urls(item, message)
        self.populate_usernames(item, message)
        doc = {"_source": item}
        return doc

    def extract_urls(self, message):
        url_pattern = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
        res = re.findall(url_pattern, message)
        if res:
            return res
        else:
            return []

    def extract_usernames(self, message):
        username_pattern = r"@([^\s:,\.]+)"
        res = re.findall(username_pattern, message)
        if res:
            return res
        else:
            return []

    def populate_urls(self, msg_object, message):
        urls = self.extract_urls(message)
        if urls:
            msg_object["urls"] = urls

    def populate_usernames(self, msg_object, message):
        usernames = self.extract_usernames(message)
        if usernames:
            msg_object["usernames"] = usernames

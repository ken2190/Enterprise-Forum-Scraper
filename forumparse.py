import argparse
import os
from glob import glob
from templates import PARSER_MAP


class Parser:
    def __init__(self, kwargs):
        self.counter = 1
        self.kwargs = kwargs

    def start(self):
        if self.kwargs.get('list'):
            print('Following parsers are available')
            for index, parser in enumerate(PARSER_MAP.keys(), 1):
                print(f'{index}. {parser}')
            return
        parser_name = self.kwargs.get('template')
        if not parser_name:
            print('Parser (-t/--template) missing')
            return
        parser = PARSER_MAP.get(parser_name.lower())
        if not parser:
            print('Message: your target name is wrong..!')
            return
        folder_path = self.kwargs.get('path')
        if not folder_path:
            print('Input Path missing')
            return
        # -----------filter files which user want to parse --------------
        files = []
        for filee in glob(folder_path+'/*'):
            if os.path.isfile(filee):
                files.append(filee)

        output_folder = self.kwargs.get('output')
        if not output_folder:
            print('Output Path missing')
            return
        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        parser(parser_name, files, output_folder, folder_path)

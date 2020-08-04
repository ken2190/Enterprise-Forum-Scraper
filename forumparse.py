import argparse
import os
from glob import glob
from templates import PARSER_MAP


class Parser:
    def __init__(self, kwargs):
        self.counter = 1
        self.kwargs = kwargs

    def print_list_template(self):
        print('Following parsers are available')
        for index, scraper in enumerate(PARSER_MAP.keys(), 1):
            print(f'{index}. {scraper}')

    def start(self):

        if self.kwargs.get('list'):
            self.print_list_template()
            return

        parser_name = self.kwargs.get('template')
        if not parser_name:
            help_message = """
            Usage: collector.py -parse [-t TEMPLATE] [-p PATH] [-o OUTPUT]\n
            Arguments:
            -t | --template TEMPLATE:  Template forum to parse
            -p | --path PATH:          Input folder path
            -o | --output OUTPUT:      Output folder path

            Optional:
            -l | --list:               List available parsers (tempalte namess)

            """
            print(help_message)
            return

        parser = PARSER_MAP.get(parser_name.lower())
        if not parser:
            print('Not found template!')
            self.print_list_template()
            return

        folder_path = self.kwargs.get('path')
        if not folder_path:
            print('Input Path missing')
            return

        self.kwargs['folder_path'] = folder_path

        # -----------filter files which user want to parse --------------
        files = []
        for filee in glob(folder_path+'/*'):
            if os.path.isfile(filee):
                files.append(filee)

        self.kwargs['files'] = files

        output_folder = self.kwargs.get('output')
        if not output_folder:
            print('Output Path missing')
            return

        self.kwargs['output_folder'] = output_folder

        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        parser(**self.kwargs)

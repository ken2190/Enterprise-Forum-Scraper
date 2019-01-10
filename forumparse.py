import argparse
import os
from glob import glob
from templates.oday_template import oday_parser
from templates.bmr_template import bmr_parser
from templates.evolution_template import evolution_parser
from templates.agora_template import agora_parser
from templates.therealdeal_template import therealdeal_parser
from templates.abraxas_template import abraxas_parser
from templates.kiss_template import kiss_parser
from templates.andromeda_template import andromeda_parser
from templates.darknetheroes_template import darknetheroes_parser
from templates.exploit_template import exploit_parser
# from blackmarket_template import blackmarket_parser

PARSER_MAP = {
    '0day': oday_parser,
    'bmr': bmr_parser,
    'evolution': evolution_parser,
    'agora': agora_parser,
    'therealdeal': therealdeal_parser,
    'abraxas': abraxas_parser,
    'kiss': kiss_parser,
    'andromeda': andromeda_parser,
    'darknetheroes': darknetheroes_parser,
    'diabolus': darknetheroes_parser,
    'exploit': exploit_parser,
}


class Parser:
    def __init__(self):
        self.counter = 1

    def get_args(self):
        parser = argparse.ArgumentParser(
            description='Parsing Forums Framework')
        parser.add_argument(
            '-t', '--template', help='Template forum to parse', required=True)
        parser.add_argument(
            '-p', '--path', help='input folder path', required=True)
        parser.add_argument(
            '-f', '--output_folder', help='output folder path', required=True)
        args = parser.parse_args()

        return args.template, args.path, args.output_folder

    def main(self):
        parser_name, folder_path, output_folder = self.get_args()

        # ------------make folder if not exist -----------------
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # -----------filter files which user want to parse --------------
        files = []
        for filee in glob(folder_path+'/*'):
            if parser_name.lower() in filee:
                files.append(filee)
        parser = PARSER_MAP.get(parser_name.lower())
        if not parser:
            print('Message: your target name is wrong..!')
            return
        parser(parser_name, files, output_folder, folder_path)


# -----run main ---
obj = Parser()
obj.main()

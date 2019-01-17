import argparse
import os
from glob import glob
from templates.oday_template import OdayParser
from templates.bmr_template import BMRParser
from templates.evolution_template import EvolutionParser
from templates.agora_template import AgoraParser
from templates.therealdeal_template import TheRealDealParser
from templates.abraxas_template import AbraxasParser
from templates.kiss_template import KissParser
from templates.andromeda_template import AndromedaParser
from templates.darknetheroes_template import DarkNetHeroesParser
from templates.exploit_template import ExploitParser
from templates.antichat_template import AntichatParser
from templates.breachforums_template import BreachForumsParser
from templates.greysec_template import GreySecParser
from templates.pandora_template import PandoraParser
from templates.thehub_template import TheHubParser
from templates.utopia_template import UtopiaParser
from templates.kickass_template import KickAssParser
from templates.darkode_template import DarkodeParser
# from templates.greyroad_template import GreyRoadParser
# from blackmarket_template import blackmarket_parser

PARSER_MAP = {
    '0day': OdayParser,
    'bmr': BMRParser,
    'evolution': EvolutionParser,
    'agora': AgoraParser,
    'therealdeal': TheRealDealParser,
    'abraxas': AbraxasParser,
    'kiss': KissParser,
    'andromeda': AndromedaParser,
    'darknetheroes': DarkNetHeroesParser,
    'diabolus': DarkNetHeroesParser,
    'exploit': ExploitParser,
    'antichat': AntichatParser,
    'breachforums': BreachForumsParser,
    'greysec': GreySecParser,
    'pandora': PandoraParser,
    'thehub': TheHubParser,
    'utopia': UtopiaParser,
    'ka': KickAssParser,
    'darkode': DarkodeParser,
    # 'greyroad': GreyRoadParser,
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

import re
from .noscrape_logger import NoScrapeLogger
# from .config import noscrape_parser_arguments
# from cli_parser import CliParser
from .db_modules.elastic import Elastic
from .main_modules.arg_verifier import ArgVerifier
from .main_modules.arg_parser import ArgParser
import os
import sys
import logging

VERSION = "2.2"


class NoScrapeV1:
    def __init__(self, args):
        self.logger = NoScrapeLogger(__name__)
        # self.parser = CliParser(description="Noscrape parsing tool", arguments=noscrape_parser_arguments)
        self.args = args

    def verify_args(self, new_config):
        scan_option = None
        if not new_config.get('dump') and not new_config.get('meta'):
            scan_option = False
        else:
            scan_option = 'meta' if new_config.get('meta') else 'dump'
            # db_type = new_config.get('type')
            # target_file = noscrape_args.get('target_file')
        return scan_option

        # scan_option, db_type, target_file = None, None, None
        # noscrape_args = self.parser.get_args()
        # if not noscrape_args.get('dump') and not noscrape_args.get('meta'):
        #     scan_option = False
        # else:
        #     scan_option = 'meta' if noscrape_args.get('meta') else 'dump'
        #     db_type = noscrape_args.get('type')
        #     target_file = noscrape_args.get('target_file')
        #
        # return scan_option, db_type, target_file

    def run(self):
        new_parser = ArgParser()
        new_config = new_parser.parse_command_line()
        self.verify_args(new_config)
        if new_config['examples']:
            new_parser.print_examples()

        if new_config['v']:
            self.logger.logger.setLevel(logging.DEBUG)

            # if new_config['type'] == 'mongo':
            #     self.run_nosql(new_config, 'mongo')
            #
            # if new_config['type'] == 'cassandra':
            #     self.run_nosql(new_config, 'cassandra')
            #
            # if new_config['type'] == 's3':
            #     self.run_s3(new_config)

        if new_config['type'] == 'es':
            self.run_es(new_config)            

        # scan_option, db_type, target_file = self.verify_args()
        # if scan_option:
        #     if db_type == 'es':
        #         self.run_es(scan_option, target_file)
        # else:
        #     self.parser.error('--either -d/--dump or -m/--meta is required')

    def find_delimeter(self, first_line):
        delimeter_options = [',', ':', '|']
        for delimeter_option in delimeter_options:
            if delimeter_option in first_line:
                return delimeter_option
        return None

    def load_from_file(self, file_path):
        # try:
        #     with open(file_path, 'r') as file_handle:
        #         first_line = file_handle.readline()
        #         delimeter = self.find_delimeter(first_line)
        # except Exception as e:
        #     raise Exception("Error when trying to open '" + file_path + "' - " + str(e))
        #
        # if delimeter is None:
        #     raise Exception("CSV delimeter of input file should be one of: [',', ':', '|']")

        try:
            result_targets = {}
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            ip, port = re.split(r'[,:]', line)
                            result_targets[ip] = port
                        except:
                            pass
            return result_targets

        except Exception as e:
            print("--Error reading target file: %s--" % file_path)
            raise e
            # self.parser.error("--Error reading target file: %s--" % target_file)

    def get_targets(self, new_config):
        target_file = new_config.get("target_file")
        if target_file:
            return self.load_from_file(target_file)
        return {}

    def create_filter_list(self, file_path):
        filter_list = []
        with open(file_path, "r") as f:
            for line in f.readlines():
                filter_list.append(
                    line.replace("\n", "").replace("\x00", "").replace("\r", "").replace("\b", "").lower())
        return filter_list

    # Prints the basic banner
    def banner(self):
        banner = '''__main__.py - A data discovery tool\nv''' + VERSION + '''\n'''
        print(banner)

    def run_es(self, new_config):
        arg_verifier = ArgVerifier(new_config)
        arg_verifier.show_es_help()
        arg_verifier.is_filter_file_specified_for_matchdump()
        # arg_verifier.is_output_file_specified_for_search()
        arg_verifier.is_target_file_specified()
        arg_verifier.is_port_specified()
        # arg_verifier.is_elastic_scrape_types_true()
        arg_verifier.is_elastic_limit_verified()

        filter_list = []
        if new_config['filter'] is not None:
            arg_verifier.try_opening_filter_file()
            filter_list = self.create_filter_list(new_config['filter'])

        out_file = None
        # if new_config['out_file'] is not None:
        #     arg_verifier.try_opening_output_file()
        #     out_file = new_config['out_file']            
        output_folder = new_config["out_folder"]            
        if output_folder:
            try:
                if os.path.exists(output_folder):
                    pass
                else:
                    os.makedirs(output_folder)                    
            except:
                print("--Could not create output folder:", output_folder)
                exit(1)

        exclude_indexes = []
        if new_config['exclude_index_file'] is not None:
            try:
                with open(new_config['exclude_index_file'], "r") as exclude_file:
                    for line in exclude_file.readlines():
                        line = line.strip()
                        if line:
                            exclude_indexes.append(line)
            except:
                print("--Error parsing exclude_index_file")
                exit(1)
        else:
            print("Exclude file not specified. Using default")        
            # default_exclude = os.path.join(os.getcwd(), "noscrape", "exclude.txt")
            default_exclude = sys.path[0]+'/noscrape/exclude.txt'
            print("Using default exclude:", default_exclude)
            try:
                with open(default_exclude, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line:
                            exclude_indexes.append(line)
            except:
                print("--Error reading default exclude file--")
                exit(1)

        # tf = new_config.get('target_file')
        # try:
        #     with open(tf, 'r') as f:
        #         pass
        # except Exception as e:
        #     print("--Error parsing target_file:", tf)

        targets = self.get_targets(new_config)
        # targets = IpTargets()
        # if argparse_data['targets'] is not None:
        #     targets.load_from_input(argparse_data['targets'], argparse_data['port'])
        #
        # if argparse_data['target_file'] is not None:
        #     targets.load_from_file(argparse_data['target_file'])

        scrape_type = new_config.get("scrape_type")
        print(exclude_indexes)
        for (ip, port) in targets.items():
            try:
                elastic = Elastic(ip=ip, port=port, exclude_indexes=exclude_indexes)
                if scrape_type == 'meta':
                    metadata = elastic.fetch_metadata()                    
                    if metadata:                        
                        self.logger.write_json(metadata, output_folder)

                        if metadata.get('_source', {}).get('ip'):
                            ip = metadata['_source']['ip']
                        elif metadata.get('ip'):
                            ip = metadata["ip"]
                        else:
                            print("IP not found.")
                            return
                        print('----------------------------------')
                        print("JSON Written in "+output_folder+'/'+ip+'.json')

                elif scrape_type == 'dump':
                    dumped_data = elastic.dump()
                    print(dumped_data)

            except Exception as e:
                print(str(e))

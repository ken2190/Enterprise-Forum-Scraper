#!/usr/bin/env python3
'''


##    ##  #######   ######   ######  ########     ###    ########  ########
###   ## ##     ## ##    ## ##    ## ##     ##   ## ##   ##     ## ##
####  ## ##     ## ##       ##       ##     ##  ##   ##  ##     ## ##
## ## ## ##     ##  ######  ##       ########  ##     ## ########  ######
##  #### ##     ##       ## ##       ##   ##   ######### ##        ##
##   ### ##     ## ##    ## ##    ## ##    ##  ##     ## ##        ##
##    ##  #######   ######   ######  ##     ## ##     ## ##        ########

A Python3 application for searching and scraping public datastorage

Installation:
	This application assumes you have python3 and pip3 installed.

	pip3 install -r requirements.txt

Sample usage:

	./__main__.py --help

This software is provided subject to the MIT license stated below.
--------------------------------------------------
	MIT License

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
--------------------------------------------------
'''

from noscrape.db_modules import MongoScrape
from noscrape.db_modules import S3BruteForce
from noscrape.db_modules import ElasticScrape
from noscrape.db_modules import CassandraScrape
from noscrape.main_modules import IpTargets
from noscrape.main_modules import ArgVerifier
from noscrape.main_modules import ArgParser

import logging
import json

VERSION = "2.0.2"


class NoScrape:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)

    # Prints the basic banner
    def banner(self):
        banner = '''__main__.py - A data discovery tool\nv''' + VERSION + '''\n'''
        print(banner)

    def create_filter_list(self, file_path):
        filter_list = []
        for line in open(file_path, "r"):
            filter_list.append(line.replace("\n", "").replace("\x00", "").replace("\r", "").replace("\b", "").lower())
        return filter_list

    # Run the MongoDB scraping module
    def run_nosql(self, argparse_data, nosql_type):
        # Verify some arguments
        arg_verifier = ArgVerifier(argparse_data)
        arg_verifier.show_nosql_help()
        arg_verifier.is_nosql_scrape_types_true()
        arg_verifier.is_target_file_specified()
        arg_verifier.is_port_specified()
        # Verify some arguments

        filter_list = []
        if argparse_data['filter'] is not None:
            arg_verifier.try_opening_filter_file()
            filter_list = self.create_filter_list(argparse_data['filter'])

        out_file = None
        if argparse_data['outFile'] is not None:
            arg_verifier.try_opening_output_file()
            out_file = argparse_data['outFile']

        if argparse_data['username'] is not None or argparse_data['password'] is not None:
            if argparse_data['authDB'] is None:
                argparse_data['authDB'] = "admin"

        # Build the tool
        if nosql_type == 'mongo':
            nosql_tool = MongoScrape(scrape_type=argparse_data['scrape_type'], username=argparse_data['username'],
                                     password=argparse_data['password'], auth_db=argparse_data['authDB'])
        elif nosql_type == 'cassandra':
            nosql_tool = CassandraScrape(scrape_type=argparse_data['scrape_type'], username=argparse_data['username'],
                                         password=argparse_data['password'])
        else:
            raise ValueError("Type Should be either 'mongo' or 'cassandra'")

        # Load the IPsa
        targets = IpTargets()
        if argparse_data['targets'] is not None:
            targets.load_from_input(argparse_data['targets'], argparse_data['port'])
        if argparse_data['targetFile'] is not None:
            targets.load_from_file(argparse_data['targetFile'])

        # Prep the output file
        first_write = True
        result_is_empty = True
        for network in targets:
            for ip in network[0]:
                try:
                    nosql_tool.set_target(str(ip), int(network[1]))
                    if not nosql_tool.test_connection():
                        # TCP connection failed
                        continue
                    if not nosql_tool.connect():
                        # Tool failed to attach to the instance
                        continue

                    results = nosql_tool.run()
                    results = nosql_tool.filter_results(results, filter_list)
                    nosql_tool.print_results(results)
                    nosql_tool.disconnect()
                    if results is not None:
                        result_is_empty = False
                    # Write out the data to the file
                    if out_file is not None:
                        write_out = open(out_file, "a")
                        if "xml" in write_out.name:
                            xml = nosql_tool.results_to_xml(results)
                            if not first_write:
                                xml = '\n'.join(xml.split("\n")[1:])
                            first_write = False
                            write_out.write(xml)
                            write_out.close()
                        elif "json" in write_out.name:
                            write_out.write(
                                "%s\n" % json.dumps(
                                    nosql_tool.results_to_json(results)
                                )
                            )

                except Exception as e:
                    self.logger.error("Error on " + str(ip) + ":" + str(network[1]) + " - " + str(e))
                    continue
        if out_file is not None and not result_is_empty:
            self.logger.error("Results written out to '" + out_file + "'")

    # Run the AWS S3 Bruteforce module
    def run_s3(self, argparse_data):
        # Verify some arguments
        arg_verifier = ArgVerifier(argparse_data)
        arg_verifier.show_s3_help()
        arg_verifier.is_access_and_secret_key_specified()
        arg_verifier.is_hitlist_file_specified()
        arg_verifier.try_opening_hitlist_file()
        # Verify some arguments

        out_file = None
        if argparse_data['outFile'] is not None:
            arg_verifier.try_opening_output_file()
            out_file = argparse_data['outFile']

        s3_tool = S3BruteForce(argparse_data['access'], argparse_data['secret'], argparse_data['hitlist'])
        logging.getLogger('boto3').setLevel(9999)
        logging.getLogger('botocore').setLevel(9999)
        logging.getLogger('nose').setLevel(9999)
        logging.getLogger('urllib3').setLevel(9999)

        if not argparse_data['v']:
            self.logger.info("Beginning S3 bucket bruteforcing - use '-v' to see progress/failures")
        else:
            self.logger.info("Beginning S3 bucket bruteforcing")

        if not s3_tool.connect():
            exit(1)

        s3_tool.runAttack(out_file)
        if argparse_data['outFile'] is not None:
            self.logger.error("Results written out to '" + argparse_data['outFile'] + "'")

    def run_es(self, argparse_data):
        # Verify some arguments
        arg_verifier = ArgVerifier(argparse_data)
        arg_verifier.show_es_help()
        arg_verifier.is_filter_file_specified_for_matchdump()
        arg_verifier.is_output_file_specified_for_search()
        arg_verifier.is_target_file_specified()
        arg_verifier.is_port_specified()
        arg_verifier.is_elastic_scrape_types_true()
        arg_verifier.is_elastic_limit_verified()
        # Verify some arguments

        filter_list = []
        if argparse_data['filter'] is not None:
            arg_verifier.try_opening_filter_file()
            filter_list = self.create_filter_list(argparse_data['filter'])

        out_file = None
        if argparse_data['outFile'] is not None:
            arg_verifier.try_opening_output_file()
            out_file = argparse_data['outFile']

        elastic_tool = ElasticScrape(scrape_type=argparse_data['scrape_type'], limit=argparse_data['limit'], keywords=filter_list)

        targets = IpTargets()
        if argparse_data['targets'] is not None:
            targets.load_from_input(argparse_data['targets'], argparse_data['port'])

        if argparse_data['targetFile'] is not None:
            targets.load_from_file(argparse_data['targetFile'])

        result_is_empty = True
        first_write = True
        for network in targets:
            for ip in network[0]:
                try:
                    elastic_tool.set_target(str(ip), int(network[1]))
                    if not elastic_tool.test_connection():
                        # TCP connection failed
                        print("failed")
                        continue
                    if not elastic_tool.connect():
                        print("connection failed")
                        # Tool failed to attach to the instance
                        continue
                    results = elastic_tool.run()

                    if argparse_data['scrape_type'] == 'dump' or argparse_data['scrape_type'] == 'matchdump':
                        continue

                    if results is not None:
                        result_is_empty = False

                    if out_file is not None:
                        write_out = open(out_file, "a")
                        text = elastic_tool.result_to_file(results)
                        if not first_write and text:
                            text = '\n\n///////////////////////////////////////////////////////////////\n\n' + text
                        first_write = False
                        write_out.write(text)
                        write_out.close()

                except Exception as e:
                    self.logger.error("Error on " + str(ip) + ":" + str(network[1]) + " - " + str(e))
                    continue

        if out_file is not None and not result_is_empty:
            self.logger.error("Results written out to '" + out_file + "'")

    def run(self):
        arg_parser = ArgParser()
        new_config = arg_parser.parse_command_line()

        if new_config['examples']:
            arg_parser.print_examples()
                  
        if new_config['v']:
            logging.getLogger().setLevel(logging.DEBUG)

        try:
            if new_config['database'] == 'mongo':
                self.run_nosql(new_config, 'mongo')

            if new_config['database'] == 'cassandra':
                self.run_nosql(new_config, 'cassandra')

            if new_config['database'] == 's3':
                self.run_s3(new_config)

            if new_config['database'] == 'es':
                self.run_es(new_config)

        except KeyboardInterrupt as e:
            self.logger.error("Caught ^C - cleaning up and exiting")
            exit(1)


if __name__ == '__main__':
    NoScrape().run()

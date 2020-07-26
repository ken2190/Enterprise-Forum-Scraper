import os
import logging

class ArgVerifier:
    def __init__(self, argparse_data):
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
        self.argparse_data = argparse_data

    def is_filter_file_specified_for_matchdump(self):
        file_path = self.argparse_data['filter']
        scrape = self.argparse_data['scrape_type']
        if scrape != 'matchdump' and file_path is not None:
            self.logger.warning("WARNING. --filter command is redundant with {} module".format(scrape))
        if scrape == 'matchdump' and file_path is None:
            self.logger.error("You should specify a filter file to use matchdump module of elasticsearch.")
            exit()

    def is_output_file_specified_for_search(self):
        file_path = self.argparse_data['outFile']
        scrape = self.argparse_data['scrape_type']
        if 'dump' in scrape and file_path is not None:
            self.logger.warning("WARNING. --output command is redundant with {} module".format(scrape))
        if scrape == 'search' and file_path is None:
            self.logger.error("You should specify an output file to use search module of elasticsearch.")
            exit()

    def try_opening_filter_file(self):
        file_path = self.argparse_data['filter']

        if os.stat(file_path).st_size == 0:
            self.logger.error("Filter file '" + str(file_path) + "' is empty. Please fill it.")
            exit(1)
        if not os.path.isfile(file_path):
            self.logger.error("Filter file '" + str(file_path) + "' cannot be found")
            exit(1)
        try:
            z = open(file_path, "r")
            z.close()
        except Exception as e:
            self.logger.error("Failed to open filter file '" + str(file_path) + "' - " + str(e))
            exit(1)

    def try_opening_output_file(self):
        file_path = self.argparse_data['outFile']
        try:
            z = open(file_path, "w+")
            z.close()
        except Exception as e:
            self.logger.error("Failed to create '" + str(file_path) + "' - " + str(e))
            exit(1)

    def is_target_file_specified(self):
        target_file = self.argparse_data['target_file']
        targets = self.argparse_data['targets']
        if target_file is None and targets is None:
            self.logger.error(
                "Missing target parameter:\n"
                "- Either --targetFile: Path to csv path that contain list of ip and port\n"
                "- Or --targets: List of ip, seperated by \",\""
            )
            exit(1)

    def is_port_specified(self):
        port = self.argparse_data['port']
        targets = self.argparse_data['targets']
        if port is None:
            self.logger.error("Please Specify the Port.")
            exit()
        if port == -1 and targets is not None:
            self.logger.error(
                "Missing port arguments:\n"
                "- Either --port: port to scan for\n"
                "- Or --targetFile: Path to csv path that contain list of ip and port")
            exit(1)

    def show_nosql_help(self):
        scrape = self.argparse_data['scrape_type']
        port = self.argparse_data['port']
        targets = self.argparse_data['targets']
        targetFile = self.argparse_data['target_file']
        if ((scrape not in ['meta', 'dump'])
            or (port == -1 and targetFile is None)
            or (targets is None and targetFile is None)):
            help_message = """
            Usage: collector.py -scan [-d DATABASE] [-st SCRAPE_TYPE] [-p PORT] [-tf TARGET_FILE]
                                      [-u USERNAME] [-pw PASSWORD] [-a AUTHDB] [-l LIMIT] [-f FILTER]
            Arguments:
            -st | --scrape_type             :  Type of scrape to run es: meta, dump
            -p | --port PORT               :  Database port
            -tf | --target_file            :  A CSV formatted list of targets host,port
            -exif | --excludeIndexFile     :  One keyword per line, all index contain these keyword will be excluded
            -u | --username                :  Username for standard authentication
            -pw | --password               :  Password for standard authentication
            -a | --authDB                  :  Database within Mongo to auth against
            -f | --filter                  :  Use to specify a list of keywords to filter within your scraped search results
            """
            print(help_message)
            exit(1)

    def show_es_help(self):
        port = self.argparse_data['port']
        targets = self.argparse_data['targets']
        targetFile = self.argparse_data['target_file']
        outputFolder = self.argparse_data['out_folder']
        scrape_type = self.argparse_data['scrape_type']
        if ((port == -1 and targetFile is None)
            or (targets is None and targetFile is None)
            or (scrape_type is None)
            or (outputFolder is None) ):
            help_message = """
            Usage: collector.py -scan [-d DATABASE] [-s SCRAPE_TYPE] [-p PORT] [-tf TARGET_FILE]
                                      [-u USERNAME] [-pw PASSWORD] [-a AUTHDB] [-l LIMIT] [-f FILTER] [-o OUPUT_FOLDER]
            Arguments:
            -st | --scrape_type             :  Type of scrape to run es: meta, dump
            -p | --port PORT               :  Database port
            -exif | --excludeIndexFile     :  One keyword per line, all index contain these keyword will be excluded
            -tf | --target_file            :  A CSV formatted list of targets host,port
            -l | --limit                   :  Number of records dumped per Elasticdump request (default & max = 10,000)
            -f | --filter                  :  Use to specify a list of keywords to filter within your scraped search results
            -o | --out_folder              :  Use to specify destination folder to save JSON file
            """
            print(help_message)
            exit(1)

    def show_s3_help(self):
        access_key = self.argparse_data['access']
        secret_key = self.argparse_data['secret']
        if access_key is None or secret_key is None:
            help_message = """
            Usage: collector.py -scan [-d DATABASE] [--access S3_ACCESS_KEY] [--secret S3_SECRET_KEY]
            Arguments:
            --access  :  S3 Access Key
            --secret  :  S3 Secret Key
            """
            print(help_message)
            exit(1)

    def is_scrape_types_true(self):
        scrape = self.argparse_data['scrape_type']
        if scrape not in ['meta', 'dump']:
            self.logger.error(
                "Missing arguments --st/scrape_type. Allowed values: [\"meta\", \"dump\"]")
            exit(1)

    def is_elastic_limit_verified(self):
        limit = self.argparse_data['limit']
        if limit < 1:
            self.logger.error(
                "Limit should be a positive number")
            exit(1)

    def is_access_and_secret_key_specified(self):
        access_key = self.argparse_data['access']
        secret_key = self.argparse_data['secret']
        if access_key is None or secret_key is None:
            self.logger.error("S3 Module missing access and/or secret keys")
            exit(1)

    def is_hitlist_file_specified(self):
        hitlist_file = self.argparse_data['hitlist']
        if hitlist_file is None:
            self.logger.error("S3 Hitlist file missing")
            exit(1)

    def try_opening_hitlist_file(self):
        hitlist_file = self.argparse_data['hitlist']
        try:
            demo_handle = open(hitlist_file, "r")
            demo_handle.close()
        except Exception as e:
            self.logger.error("Failed to open '" + str(hitlist_file) + "' - " + str(e))
            exit(1)


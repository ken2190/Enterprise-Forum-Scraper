from .noscrape_logger import NoScrapeLogger
from .config import noscrape_parser_arguments
from parser import Parser
from .db_modules.elastic import Elastic

class NoScrapeV1:
    def __init__(self, args):
        self.logger = NoScrapeLogger(__name__)
        self.parser = Parser(description="Noscrape parsing tool", arguments=noscrape_parser_arguments)
        self.args = args

    def verify_args(self):
        scan_option, db_type, target_file = None, None, None
        noscrape_args = self.parser.get_args()
        if not noscrape_args.get('dump') and not noscrape_args.get('meta'):
            scan_option = False
        else:
            scan_option = 'meta' if noscrape_args.get('meta') else 'dump'
            db_type = noscrape_args.get('type')
            target_file = noscrape_args.get('target_file')

        return scan_option, db_type, target_file

    def run(self):
        scan_option, db_type, target_file = self.verify_args()
        if scan_option:
            if db_type == 'es':
                self.run_es(scan_option, target_file)
        else:
            self.parser.error('--either -d/--dump or -m/--meta is required')

    def get_targets(self, target_file):
        try:
            result_targets = {}
            with open(target_file, 'r') as tf:
                target_lines = tf.readlines()
                for line in target_lines:
                    line = line.strip()
                    if line:
                        ip, port = line.split(",")
                        result_targets[ip] = port
            return result_targets

        except Exception as e:
            self.parser.error("--Error reading target file: %s--" % target_file)

    def run_es(self, scan_option, target_file):
        targets = self.get_targets(target_file)
        for (ip, port) in targets.items():
            elastic = Elastic(scrape_type=scan_option, ip=ip, port=port)
            if scan_option == 'meta':
                metadata = elastic.fetch_metadata()
                print(metadata)
            elif scan_option == 'dump':
                db_data = elastic.fetch_data()





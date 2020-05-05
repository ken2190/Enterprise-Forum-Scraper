import argparse


# Parses the arguments
class ArgParser():
    def parse_command_line(self):
        """This function parses and return arguments passed in"""
        databases = ["mongo", "s3", "es", "cassandra"]

        # Assign description to the help doc
        parser = CustomArgumentParser()
        parser._optionals.title = "Standard arguments"

        parser.add_argument('--database', '-d', nargs='?', help='State the type of database', choices=databases, required=True)
        parser.add_argument('--outFile', '-o', nargs='?', default=None, metavar="OutputFile", help='File to store results')
        parser.add_argument('-v', action="store_true", help='Enable verbose output')
        parser.add_argument('--examples', action="store_true", help='Print usage examples then exit')

        # Mongo and Elastic stuff
        nosql_and_elastic_options = parser.add_argument_group('MongoDB and ElasticSearch Options')
        nosql_and_elastic_options.add_argument('--targetFile', '-tf', nargs='?', metavar="TargetFile", default=None,
                                               help='A CSV formatted list of targets host,port', type=str)
        nosql_and_elastic_options.add_argument('--targets', '-t', nargs='?', metavar="Targets", default=None,
                                               help='IP or CIDR of database(s)', type=str)
        nosql_and_elastic_options.add_argument('--port', '-p', nargs='?', metavar="Port", default=-1, help='Database port',
                                               type=int)
        nosql_and_elastic_options.add_argument('--scrape_type', '-s', nargs='?', default='basic', help='Type of scrape to run')
        nosql_and_elastic_options.add_argument('--filter', '-f', nargs='?', default=None, metavar="FilterFile",
                                               help='Use to specify a list of keywords to filter within your scraped search results ')
        nosql_and_elastic_options.add_argument('--username', '-u', nargs='?', metavar="Username", default=None,
                                               help='Username for standard authentication', type=str)
        nosql_and_elastic_options.add_argument('--password', '-pw', nargs='?', metavar="Password", default=None,
                                               help='Password for standard authentication', type=str)
        nosql_and_elastic_options.add_argument('--authDB', '-a', nargs='?', metavar="AuthDB", default=None,
                                               help='Database within Mongo to auth against', type=str)
        nosql_and_elastic_options.add_argument('--limit', '-l', nargs='?', metavar="Limit", default=10,
                                               help='Number of records dumped per Elasticdump request (default & max = 10,000)',
                                               type=int)
        #
        #
        #
        # S3 Stuff
        #
        s3_opts = parser.add_argument_group('AWS Brute S3 Options')
        s3_opts.add_argument('--access', metavar="AccessKey", default=None, help='AWS Access Key', type=str)
        s3_opts.add_argument('--secret', metavar="SecretKey", default=None, help='AWS Secret Key', type=str)
        s3_opts.add_argument('--hitlist', metavar="DictionaryFile", default=None,
                             help='File containing brute-force keyword list', type=str)
        args = parser.parse_args()
        new_config = args.__dict__
        return new_config

    def print_examples(self):
        examples = "\n"
        examples += "# Mongo Module\n"
        examples += "./__main__.py -d mongo --targets 127.0.0.1 --port 27017 --scrape_type basic -v\n"
        examples += "./__main__.py -d mongo -iL targetList.txt --scrape_type basic\n"
        examples += "./__main__.py -d mongo --targets 1.1.1.1 --port 27017 --scrape_type fields --filter filter.txt -o output.xml\n"
        examples += "./__main__.py -d mongo --targets 10.20.30.0/24 --port 27017 --scrape_type fields --username admin --password admin\n"
        examples += "\n"
        examples += "# S3 Examples\n"
        examples += "./__main__.py -d s3 --access X --secret X --hitlist list.txt -o results.xml\n"
        examples += "\n"
        examples += "# Elastic Examples\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type scan\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type scan -o scan_output.txt\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type search\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type  search -o search_output.txt\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type dump\n"
        examples += "./__main__.py -d es -t 127.0.0.1 -p 9200 --scrape_type dump --limit 100\n"
        examples += "\n"
        examples += "# Cassandra Module\n"
        examples += "./__main__.py -d cassandra --targets 127.0.0.1 --port 9042 --scrape_type basic -v\n"
        examples += "./__main__.py -d cassandra -iL targetList.txt --scrape_type basic\n"
        examples += "./__main__.py -d cassandra --targets 1.1.1.1 --port 9042 --scrape_type fields --filter filter.txt -o output.xml\n"
        examples += "./__main__.py -d cassandra --targets 10.20.30.0/24 --port 9042 --scrape_type fields --username admin --password admin\n"

        print(examples)
        exit(0)


class CustomArgumentParser(argparse.ArgumentParser):
    def get_help_file_content(self):
        try:
            with open("help.txt", "r") as myfile:
                return myfile.read()
        except Exception as e:
            print(e)
            return None

    def format_help(self):
        return self.get_help_file_content()

from .NoScrapePlugin import NoScrapePlugin
from elasticsearch import Elasticsearch
import subprocess as sp
import os
import json


class ElasticScrape(NoScrapePlugin):
    def __init__(self, scrape_type=None, limit=None, keywords=None, exclude_indexes=[]):
        self.scrape_type = scrape_type
        self.limit = limit
        self.keywords = keywords
        self.exclude_indexes = exclude_indexes
        super().__init__()

    def run(self):
        if self.scrape_type == 'scan':
            return self.scan()

        if self.scrape_type == 'search':
            return self.search()

        if self.scrape_type == 'dump':
            return self.dump()

        if self.scrape_type == 'matchdump':
            return self.matchdump()

    def connect(self):
        try:
            self.DBClient = Elasticsearch([{'host': self.target, 'port': self.port}])
        except Exception as e:
            return False
        return True

    def scan(self):
        try:
            self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.target, self.port))
            results = self.DBClient.cat.indices(v=True, format='text')
            self.logger.info("----Results: {}:{}".format(self.target, self.port))
            self.logger.info(results)
            return results
        except Exception as e:
            if 'NotFoundError' in str(e):
                self.logger.error("404 not Found for the " + str(self.target) + ":" + str(self.port))
                return None
            if 'AuthorizationException' in str(e):
                self.logger.error("User is not authorized to perform this action for the " + str(self.target) + ":" + str(self.port))
                return None
            print(e)
            return None

    def search(self):
        self.logger.info("----Requesting for the mapping data for {}:{}".format(self.target, self.port))
        try:
            return self.DBClient.indices.get_mapping('*')
        except Exception as e:
            if 'NotFoundError' in str(e):
                self.logger.error("404 not Found for the " + str(self.target) + ":" + str(self.port))
                return None
            if 'AuthorizationException' in str(e):
                self.logger.error("User is not authorized to perform this action for the " + str(self.target) + ":" + str(self.port))
                return None
            print(e)
            return None

    def dump(self):
        max_elasticdump_limit = 10000
        if self.limit > max_elasticdump_limit:
            self.limit = max_elasticdump_limit
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        indexes = self.DBClient.indices.get('*')
        for index in indexes:
            for keyword in self.exclude_indexes:
                if keyword.lower() in index.lower():
                    print("Ignore index %s because contain keyword %s in exclude file." % (index, keyword))
                    continue
            print("Dumping to file for ip {}:{} and the index {}".format(self.target, self.port, index))
            elastic_dump_command = "sudo elasticdump --input=http://{}:{}/{} --output={}/{}.txt –ignore-errors --limit={}".\
                format(self.target, self.port, index, self.target, index, self.limit)
            try:
                sp.check_output(elastic_dump_command, shell=True)
            except Exception as e:
                print(e)
        return "dump"

    def matchdump(self):
        results = self.search()
        if self.is_any_keyword_in_mapping(results):
            self.dump()
        else:
            self.logger.info("----Could not find any matches in filterlist for {}:{}".format(self.target, self.port))

        return "matchdump"

    def is_any_keyword_in_mapping(self, results):
        self.logger.info("----Checking if any keyword in filter list matches for {}:{}".format(self.target, self.port))
        for keyword in self.keywords:
            if keyword in str(results).lower():
                return True
        return False

    def result_to_file(self, results):
        if self.scrape_type == 'scan':
            return "----Results: {} {}\n{} \n".format(self.target, self.port, results)

        if self.scrape_type == 'search':
            self.logger.info("----Dumping all the mapping data for {}:{}".format(self.target, self.port))
            text = "----Results: {} {}\n".format(self.target, self.port)
            text = text + json.dumps(results)
            return text





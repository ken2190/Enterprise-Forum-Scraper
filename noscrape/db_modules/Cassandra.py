from .NoScrapePlugin import NoScrapePlugin
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from cassandra.auth import PlainTextAuthProvider
from xml.etree import ElementTree as ET
from cassandra.policies import DCAwareRoundRobinPolicy


class CassandraScrape(NoScrapePlugin):
    def __init__(self, scrape_type='basic', username=None, password=None):
        self.scrape_type = scrape_type
        self.username = username
        self.password = password
        self.session = None
        super().__init__()
        pass

    def run(self):
        return self.scrape()

    def connect(self):
        if self.username is None and self.password is None:
            auth_provider = None
        else:
            auth_provider = PlainTextAuthProvider(username=self.username, password=self.password)
        self.DBClient = Cluster([self.target], port=self.port, load_balancing_policy=DCAwareRoundRobinPolicy(),
                                auth_provider=auth_provider)
        try:
            self.session = self.DBClient.connect()
        except Exception as e:
            if 'Bad credentials' in str(e):
                if self.username is None or self.password is None:
                    self.logger.error("Please specify username and password for DB " + str(self.target) + ":" + str(self.port))
                else:
                    self.logger.error("Invalid username or password on " + str(self.target) + ":" + str(self.port))
            return False

        self.session.row_factory = dict_factory
        return True

    def disconnect(self):
        if self.DBClient is not None:
            self.DBClient.shutdown()
        return True

    def scrape(self):
        db_results = {}
        # Get list of all keyspaces
        keyspaces = []
        try:
            for key in self.DBClient.metadata.keyspaces:
                keyspaces.append(key)
        except Exception as e:
            print(e)

        for keyspace in keyspaces:
            self.session.set_keyspace(keyspace)
            if 'system' in keyspace:
                continue

            db_results[keyspace] = {}

            try:
                for table_name in self.DBClient.metadata.keyspaces[keyspace].tables:
                    db_results[keyspace][table_name] = []

                    if self.scrape_type == 'fields':
                        rows = self.session.execute('SELECT * FROM {} LIMIT 1'.format(table_name))
                        try:
                            fields = list(rows[0].keys())
                        except:  # No field found
                            #print(e)
                            continue

                        db_results[keyspace][table_name] = fields

            except Exception as e:
                self.logger.error("An unexpected error occured on " + self.target + ":" + str(self.port) + " - " + str(e))
                return db_results
        return db_results

        # Filters the results based on the filter file provided
    def filter_results(self, results, keywords):
        for keyspace, tables in results.items():
            for table, fields in tables.items():
                valid_results = []
                for field in fields:
                    if len(keywords) != 0 and self.grep(field, keywords) is False:
                        continue
                    else:
                        valid_results.append(field)
                results[keyspace][table] = valid_results
        return results

    # Prints out the parsed results
    def print_results(self, results):
        if len(results) == 0:
            self.logger.debug(
                "No Keyspaces found on " + str(self.target) + ":" + str(self.port))  # Excluding the builtin/defaults
            return

        for keyspace, tables in results.items():
            self.logger.info("{Keyspace} " + keyspace)

            if len(tables) == 0:
                self.logger.info("\t" + "No tables found on '" + str(tables) + "'")
                continue

            for table, fields in tables.items():
                self.logger.info("\t" + "{Table} " + table)

                if self.scrape_type != 'fields':
                    continue

                for field in fields:
                    self.logger.info("\t\t" + "{Field} " + field)

# Takes in the results from "run" and returns the xml string to output to file
    def results_to_xml(self, results):
        parent = ET.Element('Target')
        parent.set('host', self.clean(str(self.target)))
        parent.set('port', self.clean(str(self.port)))
        parent.set('dbType', self.clean(str("cassandra")))
        parent.set('username', self.clean(str(self.username)))
        parent.set('password', self.clean(str(self.password)))

        for keyspace, tables in results.items():
            db_tree = ET.SubElement(parent, 'Keyspace')
            db_tree.set('name', self.clean(keyspace))
            for table, fields in tables.items():
                t_tree = ET.SubElement(db_tree, 'Table')
                t_tree.set('name', self.clean(table))
                for field in fields:
                    f_tree = ET.SubElement(t_tree, 'Field')
                    f_tree.set('name', self.clean(field))
        mydata = self.prettify_xml(parent)
        return mydata
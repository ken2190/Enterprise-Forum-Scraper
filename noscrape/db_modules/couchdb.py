
import logging
from datetime import datetime

import couchdb

from .no_scrape_plugin import NoScrapePlugin


class CouchDB(NoScrapePlugin):
    def __init__(self, scrape_type='basic', username=None, password=None):
        self.scrape_type = scrape_type
        self.username = username
        self.password = password
        super().__init__()
        self.logger.setLevel(logging.DEBUG)

    def connect(self):
        session = couchdb.http.Session(timeout=10)
        try:
            self.DBClient = couchdb.Server(f'http://{self.target}:{self.port}', session=session)
            list(self.DBClient)
            return self.DBClient
        except Exception:
            return False

    def disconnect(self):
        self.DBClient = None
        return True

    def filter_results(self, results, keywords):
        return results

    def print_results(self, results):
        if len(results) == 0:
            self.logger.debug("No Databases found on %s:%s",
                              self.target, self.port)
            return

    # Runs the attack
    def run(self):
        return self.scrape()

    def scrape(self):
        db_results = {}

        self.logger.debug("Enumerating DBs on %s...", self.target)

        try:
            databases = list(self.DBClient)
        except couchdb.Unauthorized:
            self.logger.error(
                "Authentication required to enumerate databases on %s:%s",
                self.target, self.port
            )
            return db_results
        except couchdb.HTTPError as exc:
            self.logger.error(
                "Unable to fetch list of databases (from %s:%s): %s",
                self.target, self.port, exc
            )
            return db_results

        self.logger.debug("%s DBs found", len(databases))

        for db_name in databases:
            db_results[db_name] = {}

            self.logger.debug("Enumerating documents in '%s' DB...", db_name)

            try:
                documents = list(self.DBClient[db_name])
            except couchdb.Unauthorized:
                self.logger.error(
                    "Authentication required to enumerate documents on %s:%s[%s]",
                    self.target, self.port, db_name
                )
                continue
            except couchdb.HTTPError as exc:
                self.logger.error(exc)
                continue

            self.logger.debug("%s documents found", len(documents))

            for document in documents:

                self.logger.debug("Enumerating fields/keys in the '%s' document...", document)

                try:
                    db_results[db_name][document] = list(self.DBClient[db_name][document])
                except couchdb.HTTPError as exc:
                    self.logger.error(exc)
                    continue

                self.logger.debug("%s fields/keys found", len(db_results[db_name][document]))

        return db_results

    def results_to_json(self, results):
        data = {
            'ip': self.clean(str(self.target)),
            'port': self.clean(str(self.port)),
            'date': str(datetime.now().date()),
            'type': str("couchdb"),
            # 'indexes': results.get("indexes"),
            "database": {
                key: value for key, value in results.items()
                # if key not in ["stats", "indexes"]
            }
        }
        if self.username:
            data.update({
                'username': self.clean(str(self.username))
            })
        if self.password:
            data.update({
                'password': self.clean(str(self.password))
            })
        #if results.get('stats'):
            #data.update({'stats': results['stats']})
        return {'_source': data}

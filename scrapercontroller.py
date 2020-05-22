import os
import requests
import settings

from forumparse import Parser
from run_scrapper import Scraper

dv_base_url = os.getenv('DV_BASE_URL')
auth_token = os.getenv('API_TOKEN')

print(dv_base_url)
print(auth_token)

headers = {
    'apiKey': auth_token
}

# query active scrapers
response = requests.get('{0}/api/scraper'.format(dv_base_url), headers=headers)
if response.status_code == 200:

    scrapers = response.json()

    # scrape / process each one
    for scraper_config in scrapers:
        template = scraper_config['template']
        output = 'output/{0}'.format(template)

        print('Scraping {}...'.format(template))
        kwargs = {
            'template': template,
            'output': 'output/{0}'.format(template)
        }
        Scraper(kwargs).do_scrape()

        print('Processing {}'.format(template))
        kwargs = {
            'template': template,
            'output': 'parse/{0}'.format(template),
            'path': 'output/{0}'.format(template)
        }
        Parser(kwargs).start()

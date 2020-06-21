
import arrow
import getopt
import json
import logging
import os
import requests
import sys

import settings
from forumparse import Parser
from run_scrapper import Scraper

dv_base_url = os.getenv('DV_BASE_URL')
headers = {
    'apiKey': os.getenv('API_TOKEN')
}
output_basedir = os.getenv('OUTPUT_DIR')
parse_basedir = os.getenv('PARSE_DIR')

logger = logging.getLogger(__name__)

def get_active_scrapers():
    """
    Retrieves the active scrapers from the Data Viper API.
    """
    response = requests.get('{}/api/scraper'.format(dv_base_url), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scrapers from API')
    return response.json()

def get_scraper(scraper_id):
    response = requests.get('{}/api/scraper/{}'.format(dv_base_url, scraper_id), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scraper by ID from API')
    return response.json()

def update_scraper(scraper, payload):
    """
    Updates the scraper in the Data Viper API.
    """
    scraper_url = '{}/api/scraper/{}'.format(dv_base_url, scraper['id'])
    requests.patch(scraper_url, data=json.dumps(payload), headers=headers)

def process_scraper(scraper):
    """
    Processes the scraper by running the scraper template and then parsing the data.
    """
    start_date = arrow.get(scraper['nextStartDate']).format('YYYY-MM-DD')
    subfolder = scraper['name']
    template = scraper['template']
    process_date = arrow.now().format('YYYY-MM-DD')

    # the output dirs for the scraper and parser
    scraper_output_dir = '{}/{}'.format(output_basedir, subfolder)
    parse_output_dir = '{}/{}'.format(parse_basedir, subfolder)

    try:
        ############################
        # Run scraper for template
        ############################
        logger.info('Scraping {} from {}...'.format(template, start_date))

        update_scraper(scraper, { 'status': 'Scraping' })

        kwargs = {
            'start_date': start_date, 
            'template': template,
            'output': scraper_output_dir
        }
        Scraper(kwargs).do_scrape()

        ############################
        # Run parser for template
        ############################
        logger.info('Processing {}'.format(template))

        update_scraper(scraper, { 'status': 'Processing' })

        kwargs = {
            'template': template,
            'output': parse_output_dir,
            'path': scraper_output_dir
        }
        Parser(kwargs).start()

        ##############################
        # Update Scraper Status / Date
        ##############################
        
        # set the scraper's next start date to the current date and clear PID
        update_scraper(scraper, { 'status': 'Idle', 'nextStartDate': process_date, 'pid': None })

    except Exception as e:
        logger.error('Failed to process scraper {}: {}'.format(scraper['name'], e))
        update_scraper(scraper, { 'status': 'Error: '.format(e), 'pid': None })

def help():
    logger.info('scraperprocessor.py -s <scraper_id>')
    
def main(argv):
    ##############################
    # Parse CLI Args
    ##############################
    try:
        opts, args = getopt.getopt(argv, "hs:", ["scraperid="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    
    scraper_id = None

    for opt, arg in opts:
      if opt == '-h':
         help()
         sys.exit()
      elif opt in ("-s", "--scraperid"):
         scraper_id = arg
         
    if scraper_id is None:
        logger.error('Missing required option scraper ID')
        help()
        sys.exit(2)

    try:
        ##############################
        # Get / Process Scraper
        ##############################
        scraper = get_scraper(scraper_id)
        process_scraper(scraper)
    except Exception as e:
        logger.error('Failed to process scraper: {}'.format(e))

if __name__ == "__main__":
   main(sys.argv[1:])

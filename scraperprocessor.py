
import arrow
import getopt
import json
import logging
import os
import requests
import subprocess
import sys

from forumparse import Parser
from run_scrapper import Scraper
from settings import (
    API_TOKEN,
    DV_BASE_URL,
    OUTPUT_DIR,
    PARSE_DIR,
)

headers = {
    'apiKey': API_TOKEN
}

# shell script to combine JSON and create archives
post_process_script = 'tools/post_process.sh'

logger = logging.getLogger(__name__)

def get_active_scrapers():
    """
    Retrieves the active scrapers from the Data Viper API.
    """
    response = requests.get('{}/api/scraper'.format(DV_BASE_URL), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scrapers from API (status={})'.format(response.status_code))
    return response.json()

def get_scraper(scraper_id):
    response = requests.get('{}/api/scraper/{}'.format(DV_BASE_URL, scraper_id), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scraper by ID from API (status={})'.format(response.status_code))
    return response.json()

def update_scraper(scraper, payload):
    """
    Updates the scraper in the Data Viper API.
    """
    scraper_url = '{}/api/scraper/{}'.format(DV_BASE_URL, scraper['id'])
    response = requests.patch(scraper_url, data=json.dumps(payload), headers=headers)
    if response.status_code != 200:
        logger.warn('Failed to update scraper (status={})'.format(response.status_code))

def process_scraper(scraper):
    """
    Processes the scraper by running the scraper template and then parsing the data.
    """
    start_date = arrow.get(scraper['nextStartDate']).format('YYYY-MM-DD')
    subfolder = scraper['name']
    template = scraper['template']
    process_date = arrow.now().format('YYYY-MM-DD')

    # the output dirs for the scraper and parser
<<<<<<< HEAD:scraperprocessor.py
    scraper_output_dir = '{}/{}'.format(output_basedir, subfolder)
    parse_output_dir = '{}/{}'.format(parse_basedir, subfolder)
=======
    scraper_output_dir = os.path.join(OUTPUT_DIR, subfolder)
    parse_output_dir = os.path.join(PARSE_DIR, subfolder)
>>>>>>> cada925208f87f3cbaea2153032da623c9f679bf:scraperprocessor.py

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
        # Post-process HTML & JSON
        ##############################
        subprocess.call([post_process_script, scraper['name'], arrow.now().format('YYYY_MM_DD')])

        ##############################
        # Update Scraper Status / Date
        ##############################
        
        # set the scraper's next start date to the current date and clear PID
        update_scraper(scraper, { 'status': 'Idle', 'nextStartDate': process_date, 'pid': None })

    except Exception as e:
        logger.error('Failed to process scraper {}: {}'.format(scraper['name'], e))
        update_scraper(scraper, { 'status': 'Error', 'pid': None })

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

import arrow
from datetime import datetime
import json
import os
import requests
import schedule
import time

import settings
from forumparse import Parser
from run_scrapper import Scraper

dv_base_url = os.getenv('DV_BASE_URL')
headers = {
    'apiKey': os.getenv('API_TOKEN')
}

def increment_start_date(start_date):
    """
    Add 1 day to the start date.
    """
    return arrow.get(start_date).shift(days=1).format('YYYY-MM-DD')

def get_active_scrapers():
    """
    Retrieves the active scrapers from the Data Viper API.
    """
    response = requests.get('{0}/api/scraper'.format(dv_base_url), headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get scrapers from API')
    return response.json()

def update_scraper(scraper, payload):
    """
    Updates the scraper in the Data Viper API.
    """
    scraper_url = '{0}/api/scraper/{1}'.format(dv_base_url, scraper['id'])
    requests.patch(scraper_url, data=json.dumps(payload), headers=headers)

def process_scraper(scraper):
    """
    Processes the scraper by running the scraper template and then parsing the data.
    """
    start_date = arrow.get(scraper['nextStartDate']).format('YYYY-MM-DD')
    template = scraper['template']
    output = 'output/{0}'.format(template)

    try:
        print('Scraping {} from {}...'.format(template, start_date))

        update_scraper(scraper, { 'status': 'Scraping' })

        kwargs = {
            'start_date': start_date, 
            'template': template,
            'output': 'output/{0}'.format(template)
        }
        Scraper(kwargs).do_scrape()

        print('Processing {}'.format(template))

        update_scraper(scraper, { 'status': 'Processing' })

        kwargs = {
            'template': template,
            'output': 'parse/{0}'.format(template),
            'path': 'output/{0}'.format(template)
        }
        Parser(kwargs).start()

        next_start_date = increment_start_date(start_date)
        print(next_start_date)
        update_scraper(scraper, { 'status': 'Idle', 'nextStartDate': next_start_date })

    except Exception as e:
        print('Failed to process scraper {}: {}'.format(scraper['name'], e))
        update_scraper(scraper, { 'status': 'Error' })

def load_and_schedule_scrapers():
    """
    Gets the config of the active scrapers from DV API and schedules each
    one at their designated time. Also re-schedules this method after
    every minute.
    """
    print('Loading and schedule scrapers...')
    schedule.clear()

    scrapers = get_active_scrapers()
    for scraper in scrapers:
        # FIXME would be nice to run in a thread/queue, but can't because scrapy uses signals
        print('Scheduling {} to run daily at {}'.format(scraper['name'], scraper['runAtTime']))
        schedule.every().days.at(scraper['runAtTime']).do(process_scraper, scraper)

    schedule.every().minute.do(load_and_schedule_scrapers)

###########################
# Main Start
###########################
try:
    load_and_schedule_scrapers()

    while True:
        schedule.run_pending()
        time.sleep(1)
        
except Exception as e:
    print('ERROR: {}'.format(e))

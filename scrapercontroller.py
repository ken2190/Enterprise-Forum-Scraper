import arrow
import json
import logging
import os
import requests
import schedule
import subprocess
import time
import sys

from settings import (
    LOG_DIR,
    PYTHON_BIN,
)

from scraperprocessor import (
    get_active_scrapers,
    update_scraper
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)

def get_log_file(scraper):
    """
    Opens a handle to the log file for the scraper and current date.
    Creates log directories if they do not exist.
    """
    dirname = os.path.join(LOG_DIR, scraper['name'])
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    log_filename = os.path.join(LOG_DIR, scraper['name'], '{}.log'.format(arrow.now().format('YYYY-MM-DD')))
    log_file = open(log_filename, 'a')
    return log_file

def check_pid(scraper):
    """
    Check if scraper's PID is set and running.
    """
    if scraper['pid'] is None:
        return False
    try:
        os.kill(scraper['pid'], 0)
        return True
    except OSError:
        return False

def spawn_scraper(scraper):
    """
    Spawns the scraper processor in a sub-process for the scraper ID.
    Output for both stdout and stderr are redirected to a dedicated log file.
    """
    try:
        # check if scraper PID is still running
        if check_pid(scraper):
            logger.warn('{} still running [PID={}'.format(scraper['name'], scraper['pid']))
            return

        log_file = get_log_file(scraper)
        script = os.path.join(os.path.dirname(__file__), 'scraperprocessor.py')
        handle = subprocess.Popen([PYTHON_BIN, script, '-s', str(scraper['id'])], stdout=log_file, stderr=log_file)
        update_scraper(scraper, { 'pid': handle.pid })
    except Exception as e:
        logger.error('Failed to spawn scraper: {}'.format(e))

def load_and_schedule_scrapers():
    """
    Gets the config of the active scrapers from DV API and schedules each
    one at their designated time. Also re-schedules this method after
    every minute.
    """
    logger.debug('Loading and schedule scrapers...')
    schedule.clear()

    scrapers = get_active_scrapers()
    for scraper in scrapers:
        try:
            if scraper.get('runNow', 0) != 0:
                logger.info('Spawning {} now!'.format(scraper['name']))
                spawn_scraper(scraper)
                update_scraper(scraper, { 'runNow': 0 })
                continue

            logger.debug('Scheduling {} to run daily at {}'.format(scraper['name'], scraper['runAtTime']))
            schedule.every().days.at(scraper['runAtTime']).do(spawn_scraper, scraper)
        except Exception:
            logger.error('Failed to schedule {}: {}'.format(scraper['name'], e))

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
    logger.error('ERROR: {}'.format(e))

#!/usr/bin/env python2
"""SOEEA Time Reporting Tool

Allows reports to be submitted from a command line interface. 

This library can be particularly effective if used to process exported data from a time tracking application.

The default configuration supports the University of Illinois time reporting web interface.

Usage:
    report_time [--date=<date>] [--hours=<hours>] [--user=<username>] [--password-file=<password_file>] [--quiet] [--five-day]

Options:
    -h --hours=<hours>  7 numbers, hours worked on Sunday - Saturday i.e. '0 8 8 8 8 8 0'
        (Default assumes 40 hour work week M-F)
    -d --date=<date>  Submit report for date other than the current due report.
        (Example: 01/21/1999)
    -f --five-day   assume a five day work week
    -u --user=<username>  The username to login as.
    -p --password-file=<password_file>  A GPG Encrypted file the contents of which are your password.
    -q --quiet  Suppress all output other than errors.
"""


# Python native
from datetime import datetime, timedelta, date
import getpass
import logging
import os
import subprocess

# Dependencies
import requests

# Included
# from doctopt import docopt
import docopt

URL         = "https://hrnet.uihr.uillinois.edu/PTRApplication/index.cfm"
OVERDUE_URL = URL + "?fuseaction=TimesheetEntryForm&Overdue=true&"
SUBMIT_URL  = URL + "?fuseaction=SubmitTimesheet" 
DATE_FORMAT = '%m/%d/%Y'

# _LOGGER
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('/tmp/report_time.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the _LOGGER
_LOGGER.addHandler(fh)
_LOGGER.addHandler(ch)

class TimeReportBrowser(object):
    def __init__(self):
        self.session = requests.session()
        self.result = self.session.get(URL)
        self.login_url = ""
    
    def is_logged_in(self):
        '''Check whether logged in'''
        if "You must log in to continue" in self.result.content:
            self.login_url = self.result.url
            return False
        else:
            return True

    def login(self):
        '''Log in to the webpage.'''
        tries = 0
        while not self.is_logged_in():
            if not args['--quiet']: 
                print "Logging in as %s..." % USERNAME
            if tries == 0 and _PASSWORD:
                if not args['--quiet']: 
                    print "Using password from file."
                pwd = _PASSWORD
            else:
                prompt = 'Username: {}, URL: {}, Password?'.format(USERNAME, LOGIN_URL)
                pwd = getpass.getpass(prompt)
            self.result = self.session.post(self.login_url, data={'USER': USERNAME, 'PASSWORD': pwd, 'queryString': 'null', 'target': URL, 'BTN_LOGIN': 'Login'}, allow_redirects=True)
            tries += 1

    def submit(self, date_string=None, hours=None, silent = False):
        '''Submit time worked during a chosen week.'''

        # Login
        self.login()

        # Go to the requested date.
        if date_string is None:
            date_string = get_recent_sunday()

        # Fetch page for the chosen date.
        url = get_url_for_date(date_string)
        self.result = self.session.get(url)

        # Implicitly convert 5 day week into 7 day week.
        if len(hours) == 5: 
            hours.insert(0, 0)
            hours.append(0)

        if len(hours) != 7:
            raise ValueError("Incorrect number of values for the week.")
        d = {}
        days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        total = 0
        for i in range(len(days)):
            d[days[i] + "TimesheetHourValue"] = int(hours[i])
            total += int(hours[i]) * 60
            minutes = hours[i] % 1
            if minutes not in [0.0, 0.25, 0.5, 0.75]:
                raise ValueError("Please only use hours rounded to the nearest quarter-hour.")
            d[days[i] + "TimesheetMinuteValue"] = minutes
            total += minutes
        d['weekTotalHours'] = int(total/60)
        d['weekTotalMinutes'] = total % 60
        self.result = self.session.post(SUBMIT_URL, data=d, allow_redirects=True)
        _LOGGER.info('Result: %s', self.result)
        _LOGGER.info('Content: %s', self.result.content)
        if "You have successfully submitted" in self.result.content:
            return "Successfully submitted %s for %s." % (str(hours), date_string)
        else:
            return "Unable to submit %s for %s. " % (str(hours), date_string) + \
                    "Have you already submitted this date?" 

args = docopt.docopt(__doc__, version='1.0')

FIVE_DAY = args['--five-day']

USERNAME = getpass.getuser()
if args['--user']: 
    USERNAME = args['--user']

_PASSWORD = None
if args['--password-file']:
    if not os.path.isfile(args['--password-file']):
        print "To create a password file, run:"
        print "  gpg --gen-key"
        print "  vim password.txt"
        print "  gpg -r email@example.com -e password.txt\n"
    _PASSWORD = subprocess.check_output('gpg --no-tty -qd %s' % args['--password-file'], shell=True).replace('\n', '')
    if not args['--quiet']: 
        print "Loaded password from %s" % args['--password-file']

def prompt_for_hours(date_string):
    '''Prompt the user for hours for a given week.'''

    # Start date.
    start_date = \
        datetime.strptime(date_string, DATE_FORMAT) 

    # As a courtesy, show end date as well. (Saturday)
    end_date = \
        datetime.strptime(date_string, DATE_FORMAT) \
        + timedelta(days=6)

    # Convert to five day week, if requested.
    if FIVE_DAY:
        # For Five day mode, show Monday, not Sunday.
        date_string = start_date.strftime(DATE_FORMAT)
        start_date += timedelta(days=1)
        # For five day mode, show Friday, not Saturday.
        end_date -= timedelta(days=1)

    choice = 'n'
    yep = ['', 'Y', 'y', 'yes', 'Yes']

    print "" # Leave a little extra space to read.
    hours_string = raw_input(
            'Hours for the week starting on {start}, ending on {end}? '.format(
                start = start_date.strftime(DATE_FORMAT),
                end = end_date.strftime(DATE_FORMAT),
                ))
    if not hours_string:
        hours_string = '0 8 8 8 8 8 0'
        if FIVE_DAY:
            hours_string = '8 8 8 8 8'

    hours = validate_hours(hours_string)

    choice = raw_input('Submit ' + str(hours) + ' for the week starting on ' + date_string + \
        '? [Y/n]')
    if not choice in yep:
        hours = prompt_for_hours(date_string)

    return hours

def get_hours_from_string(hours_string):
    return validate_hours(hours_string.split(' '))

def validate_hours(hours_string):
    try:
        hours_values = hours_string.strip().split(' ')
        hours = [float(value) for value in hours_values]

        if FIVE_DAY:
            if len(hours) != 5:
                print "Expected 5 values for Monday-Friday"
                return None
        else:
            if len(hours) != 7:
                print "Expected 7 values for Sunday-Saturday"
                return None

        return hours
    except ValueError:
        print "Error: Invalid hours provided."
        print "All values must be numbers in float format."
        print __doc__
        return None 

def get_url_for_date(date_string):
    month, day, year = [int(x) for x in date_string.split('/')]
    the_date = date(year, month, day)
    url = OVERDUE_URL + "month=" + str(the_date.month) + "&selectedWeek=" + date_string
    return url

def get_recent_sunday():
    day = datetime.now() 
    while day.strftime('%A') != 'Sunday':
        day = day - timedelta(days=1)
    return day.strftime(DATE_FORMAT)

def main():

    br = TimeReportBrowser()
    date_string = None
    hours = None

    if args['--hours']:
        hours_string = args['--hours'] 
        if hours_string:
            hours = validate_hours(hours_string)
    # FIXME - Default is string not array.
    if args['--date']:
        date_string = args['--date']

    if not date_string:
        date_string = get_recent_sunday()

    # Submit time
    br.login()
    if "Edit" in br.result.content:
        if not args['--quiet']: 
            print "Time reporting for this week is up to date."
    else:
        if not hours:
            if not args['--quiet']:
                hours = prompt_for_hours(date_string)
        outcome = br.submit(date_string, hours)
        if not args['--quiet']: 
            print outcome

        # Review overdue time
    if not "Submission of time for the following week(s) is overdue." in br.result.content:
        if not args['--quiet']: 
            print "Time reporting is up to date."
    else:
        content = br.result.content
        overdue = [x.strip() for x in content[content.find('id="pastDueWeek">'):content.find('</select>&nbsp;<input type="submit" id="getPastDueTimeEntryForm"')].split('\n') if x.strip()][1:]
        overdue = [x[x.find('month='):x.find('">')] for x in overdue]
        overdue = [x[x.find('Week=')+5:] for x in overdue]
# Strip out additional cruft.
        overdue = [x[:x.find('&CurrentWk')] for x in overdue]
        # overdue = [x[:x.find('Year=')] for x in overdue]

        print "Warning: Overdue time reports (" + str(len(overdue)) + ")."
        if len(overdue) < 10:
            print '\n'.join(overdue)

        for day in overdue:
            if not args['--quiet']:
                hours = prompt_for_hours(day)
                print br.submit(day, hours)
        if not args['--quiet']: 
            print "Time reporting is now up to date."

if __name__ == "__main__":
    main()

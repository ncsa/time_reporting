#!/usr/bin/env python2
"""SOEEA Time Reporting Tool

Allows reports to be submitted from a command line interface. 

This library can be particularly effective if used to process exported data from a time tracking application.

The default configuration supports the University of Illinois time reporting web interface.

Usage:
    report_time [--date=<date>] [--hours=<hours>] [--password-file=<password_file>]

Options:
    -h --hours=<hours>  7 numbers, hours worked on Sunday - Saturday [default: '0 8 8 8 8 8 0'] 
        (Default assumes 40 hour work week M-F)
    -d --date=<date>   Submit report for date other than the current due report.
        (Example: 01/21/1999)
    -p --password-file=<password_file> A GPG Encrypted file the contents of which are your password.
"""


# Python native
from datetime import datetime, timedelta, date
import getpass
import sys
import logging
import subprocess

# Dependencies
import requests

# Included
# from doctopt import docopt
import docopt

URL         = "https://hrnet.uihr.uillinois.edu/PTRApplication/index.cfm"
LOGIN_URL   = "https://eas.admin.uillinois.edu/eas/servlet/login.do"
OVERDUE_URL = URL + "?fuseaction=TimesheetEntryForm&Overdue=true&"
SUBMIT_URL  = URL + "?fuseaction=SubmitTimesheet" 
DATE_FORMAT = '%m/%d/%Y'

# _LOGGER
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('report.log')
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

USERNAME = getpass.getuser()
_PASSWORD = None

class TimeReportBrowser(object):
    def __init__(self):
        self.session = requests.session()
        self.result = self.session.get(URL)
    
    def is_logged_in(self):
        '''Check whether logged in'''
        if "Enterprise Authentication Service" in self.result.content:
            return False
        else:
            return True

    def login(self):
        '''Log in to the webpage.'''
        tries = 0
        while not self.is_logged_in():
            print "Logging in as %s..." % USERNAME
            if tries == 0 and _PASSWORD:
                print "Using password from file."
                pwd = _PASSWORD
            else:
                pwd = getpass.getpass('Enterprise ID Password? ')
            self.result = self.session.post(LOGIN_URL, data={'inputEnterpriseId': USERNAME, 'password': pwd, 'queryString': 'null', 'BTN_LOGIN': 'Login'}, allow_redirects=True)
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

        if len(hours) != 7:
            raise ValueError("Expected 7 values for Sunday-Saturday")
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

print args
if '--password-file' in args:
    _PASSWORD = subprocess.check_output('gpg -qd %s' % args['--password-file'], shell=True).replace('\n', '')
    print "Loaded password from %s" % args['--password-file']

# if not _PASSWORD:
#     print "To create a passwordfile, run:\ngpg --gen-key; vim report_pass.txt; gpg - e report_pass.txt"

def prompt_for_hours(date_string):
    '''Prompt the user for hours for a given week.'''

    choice = 'n'
    yep = ['', 'Y', 'y', 'yes', 'Yes']

    hours_string = raw_input('Hours for the week starting on %s? ' % date_string)
    import pdb; pdb.set_trace()
    if not hours_string:
        hours_string = '0 8 8 8 8 8 0'

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
        hours_values = hours_string.split(' ')
        hours = [float(value) for value in hours_values]

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
    
    # if '--hours' in args:
        # hours_string = args['--hours'] 
        # hours = validate_hours(hours_string)
# FIXME - Default is string not array.
    if '--date' in args:
        date_string = args['--date']

    if not date_string:
        date_string = get_recent_sunday()
  
# Submit time
    br.login()
    if "Edit" in br.result.content:
        print "Time reporting for this week is up to date."
    else:
        if not hours:
            hours = prompt_for_hours(date_string)
        print br.submit(date_string, hours)

        # Review overdue time
    if not "Submission of time for the following week(s) is overdue." in br.result.content:
        print "Time reporting is up to date."
    else:
        content = br.result.content
        overdue = [x.strip() for x in content[content.find('id="pastDueWeek">'):content.find('</select>&nbsp;<input type="submit" id="getPastDueTimeEntryForm"')].split('\n') if x.strip()][1:]
        overdue = [x[x.find('month='):x.find('">')] for x in overdue]
        overdue = [x[x.find('Week=')+5:] for x in overdue]

        print "Warning: Overdue time reports (" + str(len(overdue)) + ")."
        if len(overdue) < 10:
            print '\n'.join(overdue)

        for day in overdue:
            hours = prompt_for_hours(day)
            print br.submit(day, hours)
        print "Time reporting is now up to date."

if __name__ == "__main__":
    main()

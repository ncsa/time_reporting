#!/usr/bin/env python2
"""SOEEA Time Reporting Tool

Allows reports to be submitted from a command line interface. 

This library can be particularly effective if used to process exported data from a time tracking application.

The default configuration supports the University of Illinois time reporting web interface.

Usage:
    report_time [--date=<date>] [--hours=<hours>] 

Options:
    -h --hours=<hours>  7 numbers, hours worked on Sunday - Saturday [default: '0 8 8 8 8 8 0'] 
        (Default assumes 40 hour work week M-F)
    -d --date=<date>   Submit report for date other than the current due report.
        (Example: 01/21/1999)
"""


# Python native
from datetime import datetime, timedelta, date
import getpass
import sys
import logging

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

# LOGGER
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
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
# add the handlers to the logger
LOGGER.addHandler(fh)
LOGGER.addHandler(ch)

USERNAME = getpass.getuser()
session = requests.session()

args = docopt.docopt(__doc__, version='1.0')

def prompt_for_hours(date_string):
    '''Prompt the user for hours for a given week.'''

    choice = 'n'
    yep = ['', 'Y', 'y', 'yes', 'Yes']

    hours_string = raw_input('Hours for %s? ' % date_string)
    if not hours_string:
        hours_string = '0 8 8 8 8 8 0'

    hours = validate_hours(hours_string)

    choice = raw_input('Submit ' + str(hours) + ' for ' + date_string + \
        '? [Y/n]')
    if not choice in yep:
        hours = prompt_for_hours(date_string)

    return hours

def isLoggedIn():
    result = session.get(URL).content
    if "easFormId" in result:
        return False
    else:
        return True

def login():
    print "Logging in as %s..." % USERNAME
    pwd = getpass.getpass('Enterprise ID Password? ')
    result = session.post(LOGIN_URL, data={'inputEnterpriseId': USERNAME, 'password': pwd, 'queryString': 'null', 'BTN_LOGIN': 'Login'}, allow_redirects=True)
    return result.content

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

def submit(date_string=None, hours=None, silent = False):

    # Go to the requested date.
    if date_string is None:
        date_string = get_recent_sunday()

    # TODO Prompt for hours...

    url = get_url_for_date(date_string)
    # print url
    result = session.get(url).content

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
    result = session.post(SUBMIT_URL, data=d, allow_redirects=True)
    LOGGER.info('Result: %s', result)
    LOGGER.info('Content: %s', result.content)
    if "You have successfully submitted" in result.content:
        return "Successfully submitted %s for %s." % (str(hours), date_string)
    else:
        return "Unable to submit %s for %s. " % (str(hours), date_string) + \
                "Have you already submitted this date?" 

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
    date_string = None
    hours = None
    result = ''
    
    if '<hours>' in args:
        hours_string = args['<hours>'] 
        hours = validate_hours(hours_string)
    if '<date>' in args:
        date_string = args['<date>']

    if not date_string:
        date_string = get_recent_sunday()

# Login
    if not isLoggedIn():
        result = login()
   
# Submit time
    if "Edit" in result:
        print "Time reporting for this week is up to date."
    else:
        if not hours:
            hours = prompt_for_hours(date_string)
        print submit(date_string, hours)

        # Review overdue time
    if not "Submission of time for the following week(s) is overdue." in result:
        print "Time reporting is up to date."
    else:
        overdue = [x.strip() for x in result[result.find('id="pastDueWeek">'):result.find('</select>&nbsp;<input type="submit" id="getPastDueTimeEntryForm"')].split('\n') if x.strip()][1:]
        overdue = [x[x.find('month='):x.find('">')] for x in overdue]
        overdue = [x[x.find('Week=')+5:] for x in overdue]

        print "Warning: Overdue time reports (" + str(len(overdue)) + ")."
        if len(overdue) < 10:
            print '\n'.join(overdue)

        for day in overdue:
            hours = prompt_for_hours(day)
            print submit(day, hours)
        print "Time reporting is now up to date."

if __name__ == "__main__":
    main()

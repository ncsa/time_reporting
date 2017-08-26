#!/bin/env python3

import logging
import argparse
import getpass
import pprint
import datetime
import os

# Local Dependencies
import time_reporter
import pyexch


def process_args():
    desc = { 'description': 'SEOAA Positive Time Reporting tool.',
             'epilog': '''PYEXCH_REGEX_CLASSES = Dict
                          PYEXCH_USER = String
                          PYEXCH_AD_DOMAIN = String
                          PYEXCH_EMAIL_DOMAIN = String
                          Regex matching is always case-insensitive. 
                       '''
           }
    parser = argparse.ArgumentParser( **desc )
    parser.add_argument( '--user', help='Username' )
    parser.add_argument( '--pwdfile',
        help='Plain text passwd ***WARNING: for testing only***' )
    parser.add_argument( '--passwd', help=argparse.SUPPRESS )
    parser.add_argument( '-n', '--dryrun', action='store_true' )
    parser.add_argument( '-q', '--quiet', action='store_true' )
    parser.add_argument( '-d', '--debug', action='store_true' )
    parser.add_argument( '-o', '--once', action='store_true',
        help='Submit only one week, then exit.' )
    action = parser.add_mutually_exclusive_group( required=True )
    action.add_argument( '--csv',
        help='Format: date,M,T,W,R,F (empty col means 8-hours worked that day)' )
    action.add_argument( '--exch', action='store_true',
        help='Load data from Exchange' )
    action.add_argument( '--list-overdue', action='store_true',
        help='List overdue dates and exit' )
    defaults = { 'user': None,
                 'pwdfile': None,
                 'passwd': None,
    }
    parser.set_defaults( **defaults )
    args = parser.parse_args()
    # check user
    if not args.user:
        args.user = os.getenv( 'PYEXCH_USER' )
    if not args.user:
        args.user = getpass.getuser()
        logging.info( 'No user specified. Using "{0}".'.format( args.user ) )
    if not args.passwd:
        if not args.pwdfile:
            args.pwdfile = os.getenv( 'PYEXCH_PWD_FILE' )
        if args.pwdfile:
            # get passwd from file
            with open( args.pwdfile, 'r' ) as f:
                for l in f:
                    args.passwd = l.rstrip()
                    break
    if not args.passwd:
        # prompt user for passwd
        prompt = "Enter passwd for '{0}':".format( args.user )
        args.passwd = getpass.getpass( prompt )
#    # if no action specified, list-overdue dates
#    if not args.csv or not args.exch :
#        args.list_overdue = True
    return args


def process_csv( infile ):
    ''' Process csv file as rows with format DATE,M,T,W,R,F
        Such that values for work days are hours worked for that day
        and empty work day columns imply 8-hours (full-day)
        Returns a dict where key=date and val=list of weekday hours
    '''
    dates_hours = {}
    with open( infile, 'r' ) as f:
        for l in f:
            line = l.rstrip()
            logging.debug( "Processing line: '{0}'".format( line ) )
            parts = line.split( ',' )
            if len( parts ) != 6:
                logging.warn( "expecting 6 parts, got {0}".format( len(parts) ) )
                continue
            try:
                d = datetime.datetime.strptime( 
                    parts[0], 
                    time_reporter.Time_Reporter.DATE_FORMAT )
            except ( ValueError ) as e:
                logging.warn( "malformed date, skipping record" )
                continue
            if d.weekday() != 6:
                logging.warn( "date is not a Sunday, skipping record" )
                continue
            weekday_hours = []
            for x in parts[1:6] :
                hourdata = time_reporter.WorkdayHours( 8, 0 )
                if len( x ) > 0:
                    hourdata.full_hours = int( x )
                weekday_hours.append( hourdata )
            if len( weekday_hours ) != 5:
                logging.warn( "expected 5 workdays, got {0}".format( len( weekday_hours ) ) )
                continue
            dates_hours[ d ] =  weekday_hours
    return dates_hours


def get_sunday_for_date( indate ):
        ''' Return the date for the Sunday prior to the given date.
            SOEEA defines weeks starting with Sunday, so URL dates need to be Sunday based
        '''
        weekday = indate.weekday()
        diff = ( weekday + 1 ) % 7
        return indate - datetime.timedelta( days=diff )


def weekly_hours_worked( start_date ):
    ''' Get data from Exchange
        Convert to weekly format suitable for time_reporter.submit
    '''
    ptr_regex = { 'NOTWORK': '(sick|doctor|dr. appt|vacation|OOTO|OOO|out of the office|out of office)' }
    pyex = pyexch.PyExch( pwd=args.passwd, regex_map=ptr_regex )
    #start_date = min( overdue.keys() )
    start_datetime = datetime.datetime.combine( start_date, datetime.time() )
    daily_report = pyex.per_day_report( start_datetime )
    # convert to hours worked per day
    daily_hours = {}
    for day, data in daily_report.items():
        work_secs = max( 28800 - data[ 'NOTWORK' ], 0 )
        full_hours = int( work_secs / 3600 )
        remainder = work_secs % 3600
        qtr_hours = int( remainder / 15 )
        if ( remainder % 15 ) > 7 :
            qtr_hours += 1
        if qtr_hours > 3:
            qtr_hours = 0
            full_hours += 1
        daily_hours[ day ] = time_reporter.WorkdayHours( full_hours, qtr_hours )
    logging.debug( 'daily_hours: {0}'.format( pprint.pformat( daily_hours ) ) )
    today = datetime.date.today()
    last_sunday = get_sunday_for_date( today )
    logging.debug( "last_sunday: {0}".format( last_sunday ) )
    diff = last_sunday - start_date
    logging.debug( "diff: {0}".format( diff ) )
    # stop if attempt to report less than one week
    if diff.days < 7:
        raise SystemExit( "Nothing to report yet." )
    zero = time_reporter.WorkdayHours( 0, 0 )
    eight = time_reporter.WorkdayHours( 8, 0 )
    default_week = [ zero, eight, eight, eight, eight, eight, zero ]
    weeks = {}
    #loop over dates in range, replace default data with that from exch
    for i in range( 0, diff.days ):
        idx = i%7 #index into array of daily hours worked
        idate = start_date + datetime.timedelta( days=i )
        logging.debug( "Processing date: {0}".format( idate ) )
        if idx == 0:
            # start new week
            logging.debug( "Start new week" )
            cur_sunday = idate
            weeks[ cur_sunday ] = list( default_week )
        if idate in daily_hours:
            logging.debug( "Found match in exch data: {0}".format( daily_hours[ idate ] ) )
            weeks[ cur_sunday ][ idx ] = daily_hours[ idate ]
    return weeks



def run( args ):
    data = {}
    reporter = time_reporter.Time_Reporter( username=args.user, password=args.passwd )
    overdue = reporter.get_overdue_weeks()
    if len( overdue ) < 1:
        raise SystemExit( "You have no overdue weeks. Congratulations!" )
    if args.list_overdue:
        print( "Overdue Dates" )
        for k in sorted( overdue.keys() ):
            print( k.strftime( '%Y-%b-%d' ) )
        raise SystemExit()
    if args.csv:
        data = process_csv( args.csv )
        logging.debug( 'CSV data: {0}'.format( pprint.pformat( data ) ) )
    elif args.exch:
        data = weekly_hours_worked( start_date=min( overdue ) )
    # Walk through list of overdue dates
    for key in sorted( overdue ):
        logging.info( 'Overdue date: {0}'.format( key ) )
        if key in data:
            logging.info( 'Found match: KEY:{0} VAL:{1}'.format( key, data[ key ] ) )
            if not args.dryrun:
                reporter.submit( date=key, hours=data[ key ] )
                logging.info( 'Successfully submitted week:{0} hours:{1}'.format( key, data[ key ] ) )
            if args.once:
                raise SystemExit()
        

if __name__ == '__main__':
    logging.basicConfig( level=logging.INFO )
#    for key in logging.Logger.manager.loggerDict:
#        print(key)
    for key in [ 'weblib', 'selection', 'grab', 'time_reporter', 'requests', 'ntlm_auth', 'exchangelib', 'future_stdlib' ] :
        logging.getLogger(key).setLevel(logging.CRITICAL)
    args = process_args()
    if args.debug:
        logging.getLogger().setLevel( logging.DEBUG )
    elif args.quiet:
        logging.getLogger().setLevel( logging.WARNING )
    run( args )

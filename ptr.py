#!./ENV/bin/python

"""
Usage: ptr [options]

Options:

    --csv <CSV>           Format: date,M,T,W,R,F (empty col means 8-hours worked that day)
    --user <USERNAME>     Username
    --pfile <PASSWDFILE>  Plain text passwd ***WARNING: for testing only***
    --list-overdue        List overdue dates and exit

"""

import fileinput
import datetime
import dateutil.parser
import pprint
import logging
import getpass
import os

# From ENV
import report_time
import docopt
import mechanize


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
                d = dateutil.parser.parse( parts[0] )
            except ( ValueError ) as e:
                logging.warn( "malformed date" )
                continue
            weekday_hours = [ 8 if len(x)<1 else int(x) for x in parts[1:6] ]
            if len( weekday_hours ) != 5:
                logging.warn( "expected 5 workdays, got {0}".format( len( weekday_hours ) ) )
                continue
            dates_hours[ d ] =  weekday_hours
    return dates_hours


def check_args( args ):
    # assign user
    if not args[ '--user' ]:
        args[ '--user' ] = getpass.getuser()
    # get passwd from file
    if args[ '--pfile' ]:
        with open( args['--pfile'], 'r' ) as f:
            for l in f:
                args[ '--passwd' ] = l.rstrip()
                break
    # prompt user for passwd
    if '--passwd' not in args:
        prompt = "Enter passwd for '{0}':".format( args['--user'] )
        args[ '--passwd' ] = getpass.getpass( prompt )


def do_interactive( args ):
    # TODO: function for interactive use
    #       list overdue weeks for user (and weeks for the current month?)
    #       create a selection list to easily choose a week
    #       prompt for hours as space separated list of floats
    raise UserWarning( "Interactive use not supported yet." )


def run( args ):
    logging.debug( 'ARGS:\n{0}'.format( pprint.pformat( args ) ) )
    if args[ '--csv' ]:
        data = process_csv( args[ '--csv' ] )
        logging.debug( 'DATA:\n {0}'.format( pprint.pformat( data ) ) )
    else:
        do_interactive( args )
    reporter = report_time.TimeReportBrowser( args['--user'], args['--passwd'] )
    # Get Overdue Weeks
    logging.debug( 'PTR - about to call get_overdue_weeks' )
    overdue = reporter.get_overdue_weeks()
    if args[ '--list-overdue' ]:
        print( "Overdue Dates" )
        for k in sorted( overdue.keys() ):
            print( k.strftime( '%Y-%b-%d' ) )
        raise SystemExit()
    # Walk through list of user provided dates
    for key in sorted( data ):
        val = data[ key ]
        if key in overdue:
            logging.info( "Submitting overdue date '{0}' ... ".format( key ) )
            reporter.submit( date=key, hours=val )
        else:
            logging.warning( "User submitted date '{0}' is NOT overdue.".format( key ) )
        # Limit number of submissions

if __name__ == '__main__':
    logging.basicConfig( level=logging.DEBUG )
    args = docopt.docopt( __doc__, version='1.0' )
    check_args( args )
    run( args )

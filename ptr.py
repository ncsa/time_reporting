#!./ENV/bin/python

#TODO: replace docopt with argparse

"""
Usage: ptr [options]

Options:

    --csv <CSV>           Format: date,M,T,W,R,F (empty col means 8-hours worked that day)
    --user <USERNAME>     Username
    --pfile <PASSWDFILE>  Plain text passwd ***WARNING: for testing only***

"""

from report_time import TimeReportBrowser
import fileinput
import datetime
import dateutil.parser
import pprint
import logging

# From sample run.sh
import docopt
import mechanize
import getpass
import os


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
        do_interactive( args ):
    reporter = TimeReportBrowser( args['--user'], args['--passwd'] )
    for key in sorted( data ):
        val = data[ key ]
        reporter.submit( date=key, hours=val )

if __name__ == '__main__':
    logging.basicConfig( level=logging.DEBUG )
    args = docopt.docopt( __doc__, version='1.0' )
    check_args( args )
    run( args )

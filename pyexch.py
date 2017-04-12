import datetime
import pprint
import re
import os
import getpass
import collections
import logging

# From ENV
import tzlocal
import exchangelib

###
# Work-around for missing TZ's in exchangelib
#
# Hopefully will get fixed in https://github.com/ncsa/exchangelib/pull/1
missing_timezones = { 'America/Chicago': 'Central Standard Time' }
exchangelib.EWSTimeZone.PYTZ_TO_MS_MAP.update( missing_timezones )
#
###

simple_event = collections.namedtuple( 'SimpleEvent', [ "start",
                                                        "end",
                                                        "elapsed",
                                                        "is_all_day" ] )


class PyExch( object ):
    def __init__( self, user=None, email=None, pwd=None, regexp=None ):
        ''' User should be in DOMAIN\\USERNAME format.
        '''
        self.user = user
        self.email = email
        self.pwd = pwd
        self.regexp = regexp
        self._try_load_from_env()
        self.re = re.compile( self.regexp, re.IGNORECASE )
        self.tz = None
        self._set_timezone()
        self.credentials = exchangelib.Credentials( username=self.user, 
                                                    password=self.pwd )
        self.account = exchangelib.Account( primary_smtp_address=self.email, 
                                            credentials=self.credentials,
                                            autodiscover=True, 
                                            access_type=exchangelib.DELEGATE )
        

    def _try_load_from_env( self ):
        if not self.user:
            u = os.getenv( 'PYEXCH_USER' )
            d = os.getenv( 'PYEXCH_DOMAIN', 'UOFI' )
            if u:
                self.user = os.environ[ 'PYEXCH_USER' ]
            elif d:
                self.user = '{0}\\{1}'.format( d, getpass.getuser() )
            else:
                msg = [ 'Unable to determine user for MS Exchange account.',
                        'Not passed to constructor and not defined in env vars:',
                        "'PYEXCH_USER' or 'PYEXCH_DOMAIN'"
                      ]
                raise UserWarning( msg )
        if not self.email:
            m = os.getenv( 'PYEXCH_EMAIL' )
            if m:
                self.email = m
            else:
                u = getpass.getuser()
                dn = 'illinois.edu'
                self.email = '{0}@{1}'.format( u, dn )
        if not self.pwd:
            pfile = os.environ[ 'PYEXCH_PWD_FILE' ]
            with open( pfile ) as f:
                self.pwd = f.read().strip()
        if not self.regexp:
            default_re = '(Holiday|out|OOTO|Vacation)'
            self.regexp = os.getenv( 'PYEXCH_REGEXP', default_re )

    def _set_timezone( self ):
        tz_str = tzlocal.get_localzone()
        self.tz = exchangelib.EWSTimeZone.from_pytz( tz_str )
        pprint.pprint( [ 'LOCALTIMEZONE', self.tz ] )


    def get_date_range_filtered( self, start ):
        calendar_events = []
        cal_start = self.tz.localize( exchangelib.EWSDateTime.from_datetime( start ) )
        cal_end = self.tz.localize( exchangelib.EWSDateTime.now() )
        items = self.account.calendar.view( start=cal_start, end=cal_end )
        for item in items:
            if self.re.search( item.subject ):
                calendar_events.append( self.as_simple_event( item ) )
        return calendar_events


    def as_simple_event( self, event ):
        start = event.start.astimezone( self.tz )
        end = event.end.astimezone( self.tz )
        elapsed = end - start
        is_all_day = event.is_all_day
        return simple_event( start, end, elapsed, is_all_day )


    def daily_hours_worked( self, start ):
        raw_events = self.get_date_range_filtered( start )
        dates = {}
        for e in raw_events:
            for i in range( 0, e.elapsed.days ):
                key = e.start + datetime.timedelta( days=i )
                dates[ key.date() ] = 0
            if not e.is_all_day:
                remainder = 28800 - e.elapsed.seconds
                hours = int( max( remainder, 0 ) / 3600 )
                key = e.end
                dates[ key.date() ] = hours
        return dates


    def get_sunday_for_date( self, indate ):
        ''' Return the date for the Sunday prior to the given date.
            SOEEA defines weeks starting with Sunday, so URL dates need to be Sunday based
        '''
        weekday = indate.weekday()
        diff = ( weekday + 1 ) % 7
        return indate - datetime.timedelta( days=diff )


    def weekly_hours_worked( self, start ):
        ''' Query exchange for range of events, from "start" to today, where subject
            matches the REGEX provided to init.
            Return dict where 
                key = sunday, 
                val = list of hours worked each day that week (Sunday - Saturday)
        '''
        start_date = start.date()
        logging.debug( "start_date: {0}".format( start_date ) )
        daily_hours = self.daily_hours_worked( start )
        logging.debug( 'daily_hours: {0}'.format( pprint.pformat( daily_hours ) ) )
        today = datetime.date.today()
        last_sunday = self.get_sunday_for_date( today )
        logging.debug( "last_sunday: {0}".format( last_sunday ) )
        diff = last_sunday - start_date
        logging.debug( "diff: {0}".format( diff ) )
        # stop if attempt to report less than one week
        if diff.days < 7:
            raise SystemExit( "Nothing to report yet." )
        default_week = [ 0, 8, 8, 8, 8, 8, 0 ]
        weeks = {}
        #TODO - Create default weeks for all weeks, then loop only over exch dates
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
                logging.debug( "Found match in exch data: hours={0}".format( daily_hours[ idate ] ) )
                weeks[ cur_sunday ][idx] = daily_hours[ idate ]
        return weeks
                

if __name__ == '__main__':
    raise UserWarning( "Command line invocation unsupported" )

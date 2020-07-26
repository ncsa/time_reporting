import os
import datetime
import logging
import collections

#external dependencies
import grab
from weblib.error import DataNotFound

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('/tmp/time_reporter.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the _LOGGER
_LOGGER.addHandler(fh)
_LOGGER.addHandler(ch)


#WorkdayHours = collections.namedtuple( 'WorkdayHours', [ 'full_hours', 'qtr_hours' ] )

class WorkdayHours( object ):
    def __init__( self, full_hours, qtr_hours ):
        self.full_hours = full_hours
        self.qtr_hours = qtr_hours

    def __str__( self ):
        return "<{}(full_hours={}, qtr_hours={})>".format( 
            self.__class__.__name__,
            self.full_hours,
            self.qtr_hours
            )
    __repr__ = __str__


class Time_Reporter( object ):

    URL = "https://hrnet.uihr.uillinois.edu/PTRApplication/index.cfm"
    URL_PFX_OVERDUE = '?fuseaction=TimesheetEntryForm&Overdue=true'
    DATE_FORMAT = '%m/%d/%Y'

    def __init__( self, username, password, *a, **k ):
        self.passwd    = password
        self.user      = username
        self.g         = grab.Grab()
        self.logged_in = None
        self.last_page = None


    # OVERLOAD grab.go() AND grab.doc.submit() SO THAT LAST PAGE LOADED
    # IS ALWAYS TRACKED. THIS ALLOWS A SIMPLE FORM OF LAZY LOADING AND SHOULD HELP
    # PREVENT MULTIPLE RELOADS OF THE SAME PAGE.
    def _go( self, url, last_page=None ):
        self.g.go( url )
        self.last_page = last_page


    def _submit( self, url=None, last_page=None ):
        if url:
            self.g.submit( url=url )
        else:
            self.g.submit()
        self.last_page = last_page

    def _login( self ):
        ''' Log in to the site.
        '''
        if self.logged_in:
            return
        self.logged_in = False
        self._go( url=self.URL )
        self.g.doc.choose_form( name='Login' )
        self.g.doc.set_input( 'USER', self.user )
        self.g.doc.set_input( 'PASSWORD', self.passwd )
        self._submit( last_page='LOGIN' )
        self.g.doc.text_assert( 'View Time Reporting for ' )
        self.logged_in = True


    def _load_base( self ):
        ''' Load base page that has links for each month of this year
            as well as the selection (pull-down) list of overdue weeks
            and the selection list of weeks for the current month
        '''
        self._login()
        # Don't need to load base if last action was login
        if self.last_page in [ 'LOGIN', 'BASE' ]:
            return
        self._go( url=self.URL, last_page='BASE' )
        self.g.doc.text_assert( 'View Time Reporting for ' )


    def _load_date( self, date ):
        ''' Load the html page for a (valid) date.
        '''
        #self._load_base()
        self._login()
        # Date must be a Sunday
        if date.weekday() != 6:
            raise UserWarning( 'Date "{0}" is not a Sunday.'.format( date ) )
        today = datetime.date.today()
        if date > today:
            raise UserWarning( 'Date "{0}" is in the future.'.format( date ) )
        month = str( date.month )
        date_str = date.strftime( self.DATE_FORMAT )
        cur_yr = today.strftime( '%Y' )
        url_tail = 'month={m}&selectedWeek={w}&CurrentWkYear={y}'.format(
            m = month,
            w = date_str,
            y = cur_yr )
        url = '{0}{1}{2}'.format( self.URL, self.URL_PFX_OVERDUE, url_tail )
        self._go( url=url, last_page='LOAD_DATE' )
        self.g.doc.text_assert( 'Enter time for the week starting {0}'.format( date_str ) )


    def get_overdue_weeks( self ):
        ''' returns dict with key = Python datetime.date object
            and value = actual value (ie: month=5&selectedWeek=05/01/2016&CurrentWkYear=2016 )
        '''
        self._load_base()
        overdue_weekdates = {}
        try:
            self.g.doc.choose_form( name='frmPastDueTimesheet' )
        except ( DataNotFound ) as e:
            pass
        else:
            for elem in self.g.doc.form.inputs:
                if elem.name == 'pastDueWeek':
                    for v in elem.value_options:
                        # Parse option value ...
                        # month=9&selectedWeek=09/11/2016&CurrentWkYear=2017
                        datestr = v.split( sep='&' )[1].split( sep='=' )[-1]
                        overdue_date = datetime.datetime.strptime( datestr, self.DATE_FORMAT )
                        overdue_weekdates[ overdue_date.date() ] = v
        return overdue_weekdates


    def submit( self, date, hours ):
        ''' Submit time worked during for the week containing the specified date.
            Date must be a Python date or datetime object.
            Hours must be a Python list (of length 5 or 7, all values must be of type
            time_reporter.WorkdayHours)
            The date must be an unsubmitted week.
        '''
        _LOGGER.debug( 'Request to submit hours for date "{0}"'.format( date ) )
        # Implicitly convert 5 day week into 7 day week.
        if len( hours ) == 5:
            workday0 = time_reporter.WorkdayHours( 0, 0 )
            hours.insert( 0, workday0 )
            hours.append( workday0 )
        if len( hours ) != 7 :
            raise UserWarning( "Expected either 5 or 7 hour values, got '{0}'".format( len( hours ) ) )
        _LOGGER.debug( 'hours: {0}'.format( hours ) )
        # Get correct page
        self._load_date( date )
        # Fill in form data
        self.g.doc.choose_form( name='frmTimesheet' )
        days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        total = 0
        for i in range( len( days ) ):
            input_name = "{0}TimesheetHourValue".format( days[i] )
            hrs = hours[i].full_hours
            _LOGGER.debug( "Attempt to set form item '{0}' to '{1}'".format( input_name, hrs ) )
            self.g.doc.set_input( input_name, str( hrs ) )
            total += hrs * 60
            minutes = hours[i].qtr_hours * 0.25
            if minutes not in [0.0, 0.25, 0.5, 0.75]:
                raise ValueError(
                    "Invalid minutes '{0}'. Must be in quarter-hour increments.".format( 
                    minutes ) )
            mins = '{0:3.2f}'.format( minutes )
            input_name = "{0}TimesheetMinuteValue".format( days[i] )
            _LOGGER.debug( "Attempt to set form item '{0}' to '{1}'".format( input_name, mins ) )
            self.g.doc.set_input( input_name, mins )
            total += minutes
        # set totals fields
        totals_data = { 'WeekTotalHours': str( int( total / 60 ) ),
                        'WeekTotalMinutes': str( int( total % 60 ) ) }
        for k,v in totals_data.items():
            _LOGGER.debug( "Attempt to set form item '{0}' to '{1}'".format( k, v ) )
            self.g.doc.set_input( k, v )
        date_str = date.strftime( self.DATE_FORMAT )
        lp = 'SUBMIT_DATE_{0}'.format( date_str )
        self._submit( last_page=lp )
        self.g.doc.save( 'form.submit.response' )
        assert_str = 'You have successfully submitted your time spent on University business for the week of {0}.'.format( date_str )
        self.g.doc.text_assert( assert_str )


if __name__ == '__main__':
    print( 'Time Reporter Module not valid from cmdline' )

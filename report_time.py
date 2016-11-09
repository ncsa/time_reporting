#!/usr/bin/env python2

# Python native
import datetime
import logging
import pprint

# Dependencies
import mechanize

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
    URL = "https://hrnet.uihr.uillinois.edu/PTRApplication/index.cfm"
    FORM_NAME_OVERDUE_WEEKS = 'frmPastDueTimesheet'

    def __init__( self, username, password, *a, **k ):
        #user provided attrs
        self.passwd = password
        self.user   = username
        self.quiet = None
        for x in [ 'quiet' ]:
            if x in k:
                setattr( self, x, k[x] )
        #internal attrs
        self.result = None
        self.session = mechanize.Browser()
        self.logged_in = None
        # TODO: need a better way to update last_page (needs to be updated for EVERY open and submit
        # TODO: maybe overload seesion.open and session.submit
        self.last_page = None


    # OVERLOAD session.open() AND session.submit() SO THAT LAST PAGE LOADED
    # IS ALWAYS TRACKED. THIS ALLOWS A SIMPLE FORM OF LAZY LOADING AND SHOULD HELP
    # PREVENT MULTIPLE RELOADS OF THE SAME PAGE.
    def _open_url( self, url, last_page=None ):
        self.result = self.session.open( url )
        self.last_page = last_page


    def _submit_form( self, last_page=None ):
        self.result = self.session.submit()
        self.last_page = last_page


    def _login( self ):
        ''' INTERNAL ONLY
            Log in to the site.
        '''
        if self.logged_in:
            return
        self._open_url( self.URL )
        _LOGGER.debug("HTML Login Form: %s", self.result.read())
        self.session.select_form("Login") # select the login form
        self.session.form['USER'] = self.user # fill in the USER
        self.session.form['PASSWORD'] = self.passwd # fill in the password
        self._submit_form( last_page='LOGIN' ) # submit the completed form
        _LOGGER.debug("HTML Login Result: %s", self.result.read())
        # check for login success
        if self.result:
            if "You must log in to continue." in self.result.read():
                raise UserWarning( "Login Failed" )
        else:
            raise UserWarning( "Bad Login Page" )
        self.logged_in = True



    def get_overdue_weeks( self ):
        ''' returns dict with key = date in MM/DD/YYYY format
            and value = actual value (ie: month=5&selectedWeek=05/01/2016&CurrentWkYear=2016 )
        '''
        self._load_base()
        items = {}
        if self._search_forms( self.FORM_NAME_OVERDUE_WEEKS ):
            self.session.select_form( self.FORM_NAME_OVERDUE_WEEKS )
            select = self.session.form.find_control( "pastDueWeek" )
            for item in select.items:
                #_LOGGER.debug( "ITEM: {0}".format( item.attrs ) )
                items[ item.attrs['contents'] ] = item.attrs['value']
        else:
            _LOGGER.debug( "Overdue Timesheets form not found" )
        _LOGGER.debug( "get_overdue_weeks: returning items: {0}".format( pprint.pformat( items ) ) )
        # TODO: do we need to unselect the overdue weeks form?
        return items



    def _load_base( self ):
        ''' Load base page that has links for each month of this year
            as well as the selection (pull-down) list of overdue weeks
            and the selection list of weeks for the current month
        '''
        self._login()
        # Don't need to load base if last action was login
        if self.last_page in [ 'BASE', 'LOGIN' ]:
            return
        # no matter the date, this will error out, but gets us the links
        self._open_url( self.URL, last_page='BASE' )
        _LOGGER.debug( "HTML Load Base Result:\n{0}".format( self.result.read() ) )


    def _load_date( self, date ):
        ''' Load the html page for a data that has NOT YET BEEN SUBMITTED.
            Use load_edit() for loading a date that was already submitted once.
            Use get_overdue_weeks() to tell the difference.
        '''
        self._load_base()
        sunday = self._get_sunday_for_date( date )
        sunday_str = sunday.strftime( DATE_FORMAT )
        link_match = "month=" + str( sunday.month )
        for link in self.session.links():
            _LOGGER.debug("load_date: found link: {0}".format( link.url ) )
            if link_match in link.url:
                self.result = self.session.follow_link(link)
                _LOGGER.debug( "HTML load_date: link result: {0}".format( self.result.read() ) )
                break
        self.session.select_form("weekDropDownForm")
        self.session.form['selectedWeek'] = [ sunday_str ]
        self._submit_form( last_page='DATE' )
        result = self.result.read()
        _LOGGER.debug( "HTML Load Date Final: {0}".format( result ) )
        if 'Enter time for the week starting {0}'.format( sunday_str ) not in result:
            self.last_page = None
            raise UserWarning( "failed to load date '{0}'".format( sunday_str ) )


#    def load_edit(self, date_string):
#        self._login(date_string)
#        self.session.open(URL)
#        new_date = _get_sunday_for_date(date_string)
#        self.session.select_form("frmRetractTimesheet")
#        self.result = self.session.submit()
#        return

    def _search_forms(self, form_name):
        rv = False
        for form in self.session.forms():
            _LOGGER.debug( "search_forms: found '{0}'".format( form.name ) )
            if form.name == form_name:
                rv = True
                break
        return rv


    def submit( self, date, hours ):
        ''' Submit time worked during for the week containing the specified date.
            Date should be a Python date or datetime object
            Hours should be a Python list object
            The date must be an unsubmitted week (use edit_date for re-submitting)
        '''
        # TODO - validate date

        # Implicitly convert 5 day week into 7 day week.
        if len( hours ) == 5:
            hours.insert(0, 0)
            hours.append(0)
        if len( hours ) != 7 :
            raise UserWarning( "Expected either 5 or 7 hour values, got '{0}'".format( len( hours ) ) )

        # Get correct page
        self._load_date( date )

        # select form
        if not self._search_forms("frmTimesheet"):
            raise UserWarning( "Timesheet form not found in webpage" )
        self.session.select_form("frmTimesheet")

        for control in self.session.form.controls:
            _LOGGER.debug( 'Control: {0}'.format( control ) )
            _LOGGER.debug( "type={0}, name={1} value={2}".format( control.type, control.name, self.session[control.name] ) )

        days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        total = 0
        for i in range(len(days)):
            formkey = days[i] + "TimesheetHourValue"
            hrs = int( hours[i] )
            _LOGGER.debug( "Attempt to set form item '{0}' to '{1}'".format( formkey, hrs ) )
            self.session.form[ formkey ] = str( hrs )
            total += int(hours[i]) * 60
            minutes = float( hours[i] % 1 )
            if minutes not in [0.0, 0.25, 0.5, 0.75]:
                raise ValueError("Please only use hours rounded to the nearest quarter-hour.")
            mins = str( minutes )
            if mins == "0.0":
                mins = "0.00"
            if mins == "0.5":
                mins = "0.50"
            formkey = days[i] + "TimesheetMinuteValue"
            _LOGGER.debug( "Attempt to set form item '{0}' to '{1}'".format( formkey, mins ) )
            self.session.form[days[i] + "TimesheetMinuteValue"] = [mins]
            total += minutes

        # set totals fields writable, and then set values
        self.session.form.find_control('WeekTotalHours').readonly = False
        self.session.form['WeekTotalHours'] = str(int(total/60))
        self.session.form.find_control('WeekTotalMinutes').readonly = False
        self.session.form['WeekTotalMinutes'] = str(total % 60)
 
        # disable btnSave and ensure btnSubmit is set
        self.session.form.find_control('btnSave').disabled = True
        self.session.form['btnSubmit'] = "Submit"

        # create submit coord fields and run fixup to add them
        # don't know if we need these
        self.session.form.new_control('text', 'btnSubmit.x',{'value':'32'})
        self.session.form.new_control('text', 'btnSubmit.y',{'value':'10'})
        self.session.form.fixup()

        _LOGGER.debug("formstuff: {0}".format( self.session.form ) )
        #submit the completed form
        self.result = self.session.submit()
        content = self.result.read()
        _LOGGER.debug("Submit Result: {0}".format( content ) )
        if "You have successfully submitted" not in content:
            raise UserWarning( "Error submitting hours '{0}' for date '{1}'".format( hours, date ) )
        _LOGGER.info( "Successfully submitted hours '{0}' for date '{1}'.".format( hours, date ) )


#    def get_url_for_date( self, the_date ):
#        ''' Return the URL that will load the page containing the given date.
#            NOTE: SOEEA defines weeks starting with Sunday, so URL will usually not
#            include the specified date, but rather, the date of the Sunday prior to
#            the specified date.
#        '''
#        OVERDUE_URL = self.URL + "?fuseaction=TimeSheetEntryForm&Overdue=false&"
#        date_string = self._get_sunday_for_date( the_date ).strftime( DATE_FORMAT )
#        url = OVERDUE_URL + "month=" + str(the_date.month) + "&selectedWeek=" + date_string
#        return url


    def _get_sunday_for_date( self, the_date ):
        ''' Return the date for the Sunday prior to the given date.
            SOEEA defines weeks starting with Sunday, so URL dates need to be Sunday based
        '''
        day = the_date - datetime.timedelta( days=0 )
        while day.strftime( '%A' ) != 'Sunday':
            day = day - datetime.timedelta( days=1 )
        return day


if __name__ == "__main__":
    raise SystemExit( "Can't run from cmdline" )

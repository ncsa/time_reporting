Report Time Tool
=================

Installing 
------------
Installation::

    git clone https://github.com/edthedev/time_reporting.git
    cd time_reporting
    ./setup.sh

To run the application::

    ./run.sh
    # See below for command line options.

Updating
---------
You can use Git to update to the latest release::

    cd time_reporting
    git pull

Using
------
Running in command line interactive mode::

    cd time_reporting
    ./run.sh

Full unix-style usage details:: 

    ./run.sh [--date=<date>] [--hours=<hours>] [--user=<username>] [--password-file=<password_file>] [--quiet] [--five-day]

Options::

    -h --hours=<hours>  7 numbers, hours worked on Sunday - Saturday i.e. '0 8 8 8 8 8 0'
        (Default assumes 40 hour work week M-F)
    -d --date=<date>  Submit report for date other than the current due report.
        (Example: 01/21/1999)
    -f --five-day   assume a five day work week
    -u --user=<username>  The username to login as.
    -p --password-file=<password_file>  A GPG Encrypted file the contents of which are your password.
    -q --quiet  Suppress all output other than errors.

Automatic Import
-----------------
The ideal use for Time Reporter is to export data tracked in a live time tracking system, and submit it automatically.

If your department uses the My.CITES Vacation/Sick Leave benefits system, there is a useful report at: 
https://my.cites.illinois.edu/vacation/printreport.asp

Example using Python to submit data for a single day::

    from report_time import TimeReportBrowser

    reporter = TimeReportBrowser()
    reporter.login() # Will prompt for password.
    args = {
        'date_string': '01/21/1999', # Should be a Sunday that starts a work week.
        'hours' = [0, 8, 8, 8, 8, 8, 0], # Hours each day for Sunday-Saturday
    }
    report.submit(**args)

Example Excel CSV named time_data.csv::

    01/21/1999, 0:8:8:8:8:8:0, Forty hour work week.
    01/28/1999, 0:0:0:8:8:8:0, Vacation day on Monday and Tuesday

Example Python to automate submission from an Excel CSV file::

    from report_time import TimeReportBrowser

    reporter = TimeReportBrowser()
    reporter.login() # Will prompt for password.

    f = open('time_data.csv', 'r')
    lines = f.readlines() 
    f.close()

    args = {}
    for line in lines:
        data = ','.split(line)
        args['date_string'] = data[0]
        args['hours'] = data[1].split(':')
        report.submit(**args)

Report Time Tool
=================

Installation::

    git clone https://github.com/edthedev/time_reporting.git
    cd time_reporting
    ./report_time.py # See usage below.

Usage::

    report_time.py [--date=<date>] [--hours=<hours>] [--user=<username>] [--password-file=<password_file>] [--quiet] [--five-day]

Options::

    -h --hours=<hours>  7 numbers, hours worked on Sunday - Saturday i.e. '0 8 8 8 8 8 0'
        (Default assumes 40 hour work week M-F)
    -d --date=<date>  Submit report for date other than the current due report.
        (Example: 01/21/1999)
    -f --five-day   assume a five day work week
    -u --user=<username>  The username to login as.
    -p --password-file=<password_file>  A GPG Encrypted file the contents of which are your password.
    -q --quiet  Suppress all output other than errors.

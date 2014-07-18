Report Time Tool
=================

Installing 
------------

User Installation::

    git clone https://github.com/edthedev/time_reporting.git
    cd time_reporting
    pip install -r requirements.txt
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

Contributing
-------------

Get the source::

    git clone https://github.com/edthedev/time_reporting.git
    cd time_reporting

(Optional) Bring up a Vagrant VM::

    cd time_reporting/deploy
    vagrant up
    vagrant ssh
    cd /source

Create a virtual environment::

   virtualenv venv 

Install the required libraries into the virtual environment::

   source venv/bin/activate
   pip install -r requirements.txt

I'm not completely certain what the point is, but we can create a Wheel out of the requests module.
Maybe we can use this when creating a nicely packed download for Mac users...?::

   >virtualenv venv 
   >source venv/bin/activate
   >pip wheel -r requirements.txt
   Downloading/unpacking requests==2.3.0 (from -r requirements.txt (line 1))
   Downloading requests-2.3.0-py2.py3-none-any.whl (452kB): 452kB downloaded
   Saved ./wheelhouse/requests-2.3.0-py2.py3-none-any.whl
   > ???
   > PROFIT!


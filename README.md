# Positive Time Reporting Tool For SOEEA
(State Officials and Employees Ethics Act)

# Requirements
* Python3
* The following dependencies will be installed by *setup.sh*
  * Grab (https://pypi.python.org/pypi/grab)
  * Exchangelib (https://pypi.python.org/pypi/exchangelib/)

# Installation
1. git clone https://github.com/ncsa/time_reporting.git
1. cd time_reporting
1. ./setup.sh

# Usage
```
usage: ptr.py [-h] [--user USER] [--pwdfile PWDFILE]
              (--csv CSV | --exch | --list-overdue)

SEOAA Positive Time Reporting tool.

optional arguments:
  -h, --help         show this help message and exit
  --user USER        Username
  --pwdfile PWDFILE  Plain text passwd ***WARNING: for testing only***
  --csv CSV          Format: date,M,T,W,R,F (empty col means 8-hours worked
                     that day)
  --exch             Load data from Exchange
  --list-overdue     List overdue dates and exit
```

## List overdue dates
```
run.sh --list-overdue
```

## Submit overdue timesheets using data from Exchange
```
run.sh --exch
```

## Submit overdue timesheets using data from CSV file
```
run.sh --csv /path/to/csvfile.csv
```

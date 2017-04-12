# Positive Time Reporting Tool For SOEEA
State Officials and Employees Ethics Act

This is a complete re-write from original sources, but still, would not have been possible without the examples and ideas from those who wrote before me.  Kudos.  I stand on the shoulders of giants.

# Requirements
* Python3
* The following dependencies will be installed by *setup.sh*
  * Grab (https://pypi.python.org/pypi/grab)
  * Exchangelib (https://pypi.python.org/pypi/exchangelib/)

# Installation
1. git clone https://github.com/ncsa/time_reporting.git
1. cd time_reporting
1. ./setup.sh

## Installation Troubleshooting
OpenSSL issues
```
pycurl: libcurl link-time ssl backend (<library>) is different from compile-time ssl backend (<library> or "none/other")
```
If you get an error similar to the above, edit `setup.sh` to export the specific `link-time` backend specified in the error message and try again.

See also: http://stackoverflow.com/questions/21096436/ssl-backend-error-when-using-openssl

See also: http://stackoverflow.com/questions/21487278/ssl-error-installing-pycurl-after-ssl-is-set

# Usage
```
usage: ptr.py [-h] [--user USER] [--pwdfile PWDFILE] [-n] [-q] [-d] [-o]
              (--csv CSV | --exch | --list-overdue)

SEOAA Positive Time Reporting tool.

optional arguments:
  -h, --help         show this help message and exit
  --user USER        Username
  --pwdfile PWDFILE  Plain text passwd ***WARNING: for testing only***
  -n, --dryrun
  -q, --quiet
  -d, --debug
  -o, --once         Submit only one week, then exit.
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

## Submit only one (oldest) overdue week
```
run.sh --exch -o 
```

## Check data without submitting (dry) run
```
run.sh --exch -n
```

## Submit overdue timesheets using data from CSV file
```
run.sh --csv /path/to/csvfile.csv
```

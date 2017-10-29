# Positive Time Reporting Tool For SOEEA
State Officials and Employees Ethics Act

This is a complete re-write from original sources, but still, would not have been possible without the examples and ideas from those who wrote before me.  Kudos.  I stand on the shoulders of giants.

# Dependencies
* Python >= 3.6
* The following dependencies will be installed by *setup.sh*
  * Grab (https://pypi.python.org/pypi/grab)
  * Exchangelib (https://pypi.python.org/pypi/exchangelib/)

# Usage
This tool can be used in two possible ways: Docker and Python VirtualEnv

## Docker
TODO

## Python VirtualEnv
1. git clone https://github.com/ncsa/time_reporting.git
1. cd time_reporting
1. ./setup.sh

### VirtualEnv Installation Troubleshooting
OpenSSL issues
```
pycurl: libcurl link-time ssl backend (<library>) is different from compile-time ssl backend (<library> or "none/other")
```
If you get an error similar to the above, edit `setup.sh` to export the specific `link-time` backend specified in the error message and try again.

See also: http://stackoverflow.com/questions/21096436/ssl-backend-error-when-using-openssl

See also: http://stackoverflow.com/questions/21487278/ssl-error-installing-pycurl-after-ssl-is-set

# Usage
## Setup Environment Variables
* NETRC
  * Path to a _netrc_ formatted file
  * Default: ~/.netrc
* PYEXCH_REGEX_JSON
  * JSON formatted string with key _NOTWORK_ and value regex string
  * Default: '{"NOTWORK": "(sick|doctor|dr. appt|vacation|OOTO|OOO|out of the office|out of office)"}'

## Test program setup and execution
```
./run.sh --help
```

## Test connectivity to Positive Time Reporting website
```
run.sh --list-overdue
```

## Test connectivity to Exchange
```
run.sh --exch -n
```

## Submit one PTR report (oldest missing report)
```
run.sh --exch -o 
```

## Submit all overdue timesheets using data from Exchange
```
run.sh --exch
```

## Test CSV formatting
```
run.sh --csv /path/to/csvfile.csv -n
```

## Submit overdue timesheets using data from CSV file
```
run.sh --csv /path/to/csvfile.csv
```

# Format of **.netrc** file
Netrc file should follow 
[standard formatting rules](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html).

## Expected Keys
* IL_PTR
  * User and password to login to the SOEEA (PTR) website
  * Required parameters
    * login
    * password
* EXCH
  * Used by [pyexch](https://github.com/andylytical/pyexch) to access Exchange calendar
  * Required parameters
    * login
      * for *@illinois.edu*, format should be *user@domain*
      * other exchange implementations may require the *domain\user*  format
    * account
      * format should be *user@domain*
    * password

## Sample Netrc
```
machine IL_PTR
login myvslusername
password myvslpassword

machine EXCH
login myexchusername@illinois.edu
password myexchpasswd
account myexchusername@illinois.edu
```

# Customize regular expression to match Exchange events
Regex matching is always case-insensitive.

Default value is
PYEXCH_REGEX_JSON='{"NOTWORK":"(sick|doctor|dr. appt|vacation|OOTO|OOO|out of the office|out of office)"}'
Regex is used to match events in Exchange that represent time not worked (such as
vacation, out of office, holiday, sick, etc...). Matching is always case-insensitive.
 The regex searches the event *subject*.
```
export PYEXCH_REGEXP='{"NOTWORK":"(sick|vacation)"}'
run.sh --exch --dryrun
```

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
1. `curl -o ~/ptr_as_docker.sh https://raw.githubusercontent.com/ncsa/time_reporting/master/docker_run.sh`
1. Edit `~/ptr_as_docker.sh` to set evnironment variables
1. `~/ptr_as_docker.sh`
1. Inside docker container
   1. `./run.sh --help`
   1. `./run.sh --list-overdue`
   1. `./run.sh -n --exch`
   1. `./run.sh --exch`

## Python VirtualEnv
1. git clone https://github.com/ncsa/time_reporting.git
1. cd time_reporting
1. ./setup.sh
1. ./run.sh --help

### VirtualEnv Installation Troubleshooting
#### OpenSSL issues
```
pycurl: libcurl link-time ssl backend (<library>) is different from compile-time ssl backend (<library> or "none/other")
```
If you get an error similar to the above, edit `setup.sh` to export the specific `link-time` backend specified in the error message and try again.

See also: http://stackoverflow.com/questions/21096436/ssl-backend-error-when-using-openssl

See also: http://stackoverflow.com/questions/21487278/ssl-error-installing-pycurl-after-ssl-is-set

#### PyCurl Issues
Error:
```
Collecting pycurl (from -r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/ef/05/4b773f74f830a90a326b06f9b24e65506302ab049e825a3c0b60b1a6e26a/pycurl-7.43.0.5.tar.gz
    Complete output from command python setup.py egg_info:
    Traceback (most recent call last):
      File "/tmp/pip-build-1tm87912/pycurl/setup.py", line 234, in configure_unix
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      File "/usr/lib/python3.6/subprocess.py", line 729, in __init__
        restore_signals, start_new_session)
      File "/usr/lib/python3.6/subprocess.py", line 1364, in _execute_child
        raise child_exception_type(errno_num, err_msg, err_filename)
    FileNotFoundError: [Errno 2] No such file or directory: 'curl-config': 'curl-config'

```
Fix:
```
sudo apt-get install libssl-dev libcurl4-openssl-dev python3-dev
```
See also: https://github.com/pycurl/pycurl/issues/596

# Usage
## Setup Environment Variables
* NETRC
  * Path to a [netrc](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html) formatted file
  * Default: ~/.netrc
* PYEXCH_REGEX_JSON
  * [JSON dictionary](https://www.w3resource.com/JSON/structures.php) formatted string with key _NOTWORK_ and value regex string
  * No Default. This value is required. An example is below:
      * `export PYEXCH_REGEX_JSON='{"NOTWORK": "(sick|doctor|dr. appt|vacation|PTO|paid time off|personal day)"}'`

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
      * for *illinois.edu*, format should be *user@domain*
      * other exchange implementations may require the *domain\user*  format
    * account
      * format should be *user@domain*
    * password

## Sample Netrc
```
machine IL_PTR
login myptrusername
password myptrpassword

machine EXCH
login myexchusername@illinois.edu
password myexchpasswd
account myexchusername@illinois.edu
```

# Customize regular expression to match Exchange events
Regex matching is always case-insensitive.

There is no default, a value must be provided. A sample is:
```
PYEXCH_REGEX_JSON='{"NOTWORK":"(sick|doctor|dr. appt|vacation|OOTO|OOO|out of the office|out of office)"}'
```

Regex is used to match events in Exchange that represent time not worked (such as
vacation, out of office, holiday, sick, etc...). Matching is always case-insensitive.
 The regex searches the event *subject*.
```
export PYEXCH_REGEX_JSON='{"NOTWORK":"(sick|vacation)"}'
run.sh --exch --dryrun
```

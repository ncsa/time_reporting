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
## Cmdline Usage
```
run.sh --help
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

See also: [ptr.py](ptr.py)

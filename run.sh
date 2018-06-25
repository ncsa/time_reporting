#/bin/bash

# Try to use python from virtualenv if it exists, else use system version
py3=env/bin/python3
[[ -x "$py3" ]] || py3=$( which python3 )

# setup pythonpath to include all dirs inside 'lib/'
parts=( $PYTHONPATH )
for d in lib/*; do
    parts+=( $( readlink -e $d ) )
done
OIFS="$IFS"
IFS=":"; PYPATH="${parts[*]}"
IFS="$OIFS"

trace_ignores='/usr/local/lib/python3.6'

PYTHONPATH="$PYPATH" \
$py3 ptr.py "$@"
#$py3 -m trace --ignore-dir="$trace_ignores" -t ptr.py "$@"

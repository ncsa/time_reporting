#/bin/bash

# setup pythonpath to include all dirs inside 'lib/'
parts=( $PYTHONPATH )
for d in lib/*; do
    parts+=( $( readlink -e $d ) )
done
OIFS="$IFS"
IFS=":"; PYPATH="${parts[*]}"
IFS="$OIFS"

PYTHONPATH="$PYPATH" \
PYEXCH_AD_DOMAIN=UOFI \
PYEXCH_EMAIL_DOMAIN=illinois.edu \
python3 ptr.py "$@"

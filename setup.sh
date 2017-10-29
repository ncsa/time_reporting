#/bin/bash

# Get Python
read pycmd < <( ./get_py_assert_min_version.sh 3 )
rc=$?
if [[ $rc -ne 0 ]] ; then
    echo "Fatal Errors: while finding python"
    exit $rc
fi
if [[ -z "$pycmd" ]] ; then
    echo "Oops, where's python?"
    exit 99
fi

# Setup Virtual Environment
$pycmd -m venv env
./env/bin/pip install -r requirements.txt

##Fix pycurl library
#./env/bin/pip3 uninstall pycurl
#export PYCURL_SSL_LIBRARY=nss
#./env/bin/pip3 install --compile pycurl

# Update git submodules
git submodule update --init

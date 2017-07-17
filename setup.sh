#/bin/bash
py3=$( which python3 )
if [[ -z "$py3" ]] ; then
    echo "Python3 Required"
    exit 1
fi
python3 -m venv ENV
./ENV/bin/pip3 install -r requirements.txt

#Fix pycurl library
./ENV/bin/pip3 uninstall pycurl
export PYCURL_SSL_LIBRARY=nss
./ENV/bin/pip3 install --compile pycurl

# Update git submodules
git submodule update --init

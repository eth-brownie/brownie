#!/bin/bash


OS="`uname`"
PY="python3"

cd /usr/local/lib
git clone --depth=1 https://github.com/HyperLink-Technology/brownie

case "$OS" in 'Linux')
    chown "$USER:$USER" brownie -R
    case "`which python3.6`" in "") ;; *) PY="python3.6";; esac
    case "`which python3.7`" in "") ;; *) PY="python3.7";; esac
;; esac

PY_VER=`$PY -c 'import sys; print(sys.version_info[1])'`

if (( $PY_VER < 6 ))
then
echo "ERROR: Brownie requires python3.6 or greater."
exit 1
fi

cd brownie
$PY -m venv venv
venv/bin/pip install wheel
venv/bin/pip install -r requirements.txt

echo '#!/bin/bash' > /usr/local/bin/brownie
echo 'source /usr/local/lib/brownie/venv/bin/activate' >> /usr/local/bin/brownie
echo 'python /usr/local/lib/brownie "$@"' >> /usr/local/bin/brownie
chmod +x /usr/local/bin/brownie

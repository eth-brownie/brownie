#!/bin/bash

OS="`uname`"
PY="python3"

cd /usr/local/lib
sudo rm -f -r brownie
sudo git clone --depth=1 --no-single-branch https://github.com/HyperLink-Technology/brownie

case "$OS" in 'Linux')
    sudo chown "$USER:$USER" brownie -R
    case "`which python3.6`" in "") ;; *) PY="python3.6";; esac
    case "`which python3.7`" in "") ;; *) PY="python3.7";; esac
;; esac

PY_VER=`$PY -c 'import sys; print(sys.version_info[1])'`

if [ "$PY_VER" -lt "6" ]
then
echo "ERROR: Brownie requires python3.6 or greater."
exit 1
fi

cd brownie
git checkout --track origin/develop
git checkout master
$PY -m venv venv
venv/bin/pip install wheel
venv/bin/pip install -r requirements.txt

echo '#!/bin/bash
source /usr/local/lib/brownie/venv/bin/activate
python /usr/local/lib/brownie "$@"' | sudo tee /usr/local/bin/brownie
sudo chmod +x /usr/local/bin/brownie

echo "Brownie has installed successfully! Type 'brownie --help' to get started."

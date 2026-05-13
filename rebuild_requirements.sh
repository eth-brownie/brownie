#!/bin/bash
cd `dirname $0`

# eth-brownie
rm -f requirements.txt
pip-compile --strip-extras \
    --rebuild \
    --no-emit-options  \
    --index-url=http://localhost:9090 \
    --trusted-host=localhost \
    requirements.in

rm -f requirements-dev.txt
pip-compile --strip-extras \
    --rebuild \
    --no-emit-options  \
    --index-url=http://localhost:9090 \
    --trusted-host=localhost \
    requirements-dev.in

echo "  === requirements.txt ==="
diff -y ../vici-slingshot2/temp-requirements.txt ./requirements.txt | grep "^[a-zA-Z]" | grep "|"

echo
echo " === requirements-dev.txt ==="
diff -y ../vici-slingshot2/temp-requirements-dev.txt ./requirements-dev.txt | grep "^[a-zA-Z]" | grep "|"
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

echo "  === requirements.txt ==="
diff -y ../vici-slingshot2/temp-requirements.txt ./requirements.txt | grep "^[a-zA-Z]" | grep "|"
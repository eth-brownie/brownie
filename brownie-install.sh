#!/bin/bash

cd /usr/local/lib
git clone --depth=1 https://github.com/iamdefinitelyahuman/brownie
chmod -R 777 /usr/local/lib/brownie
cd brownie
virtualenv -p /usr/bin/python3.7 env
env/bin/pip install -r requirements.txt

echo '#!/bin/bash' > /usr/local/bin/brownie
echo 'source /usr/local/lib/brownie/env/bin/activate' >> /usr/local/bin/brownie
echo 'python /usr/local/lib/brownie "$@"' >> /usr/local/bin/brownie
chmod +x /usr/local/bin/brownie

cd /usr/local/lib
git clone --depth=1 https://github.com/iamdefinitelyahuman/brownie
chmod -R 777 /usr/local/lib/brownie
cd brownie
virtualenv -p /usr/bin/python3.7 env
source env/bin/activate
pip install -r requirements.txt
deactivate

echo '#!/bin/bash' > /usr/local/bin/brownie
echo 'source env/bin/activate' >> /usr/local/bin/brownie
echo 'python /usr/local/lib/brownie "$@"' >> /usr/local/bin/brownie
echo 'deactivate' >> /usr/local/bin/brownie
chmod +x /usr/local/bin/brownie

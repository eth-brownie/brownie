cd /usr/local/lib
git clone --depth=1 https://github.com/iamdefinitelyahuman/brownie
chmod -R 777 /usr/local/lib/brownie

echo '#!/bin/bash' > /usr/local/bin/brownie
echo 'python3 /usr/local/lib/brownie "$@"' >> /usr/local/bin/brownie
chmod +x /usr/local/bin/brownie

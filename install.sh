echo '#!/bin/bash' > /usr/local/bin/brownie
echo 'python3 /usr/local/lib/brownie "$@"' >> /usr/local/bin/brownie

chmod +x /usr/local/bin/brownie
mkdir -p /usr/local/lib/brownie
cp * /usr/local/lib/brownie -r
chmod -R 777 /usr/local/lib/brownie
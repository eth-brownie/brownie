.. _nonlocal-networks:

====================
Non-local Networks
====================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can also connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

Warning
========================
Before you go any farther, consider that connecting to non-local networks can potentially expose your private keys if you aren't careful:
* When you are interacting with mainnet, make sure you verify all of the details of any transactions you sign/send before you send them. Brownie can't protect you from sending ETH to the wrong address, sending too much, etc. 
* Always protect your private keys.  Don't leave them lying around unencrypted!

Register with Infura
========================
Before you can connect to a non-local network, you need access to a remote Ethereum node that supports JSON RPC over HTTP.  `Infura <https://infura.io>`__ is one such option.  Once you register and create a project, Infura will provide you URLs with the API key that can be leveraged to access the given network.

Non-local Network Configuration
================================

The connection settings for non-local networks must be defined in ``brownie-config.json``.

First, for each network you want to configure, create a new section in the network.networks section as below:

.. code-block:: javascript
    "networks": {
        .
        .
        "ropsten": {
            "host": "http://ropsten.infura.io/v3/[yourInfuraApiKey]"
        }
        "rinkeby":...
        .
        .
    }

If you want to change the default network that brownie connects to, you need to update the network.default field as below:

.. code-block:: javascript
    "network": {
        "default": "ropsten",
        .
        .
    }

Launching and Connecting
========================

Brownie will connect to whichever network is set as "default" in ``brownie-config.json``.  

To connect to any other network that has been defined in ``brownie-config.json``, you must specify the `--network` flag when launching Brownie as below:
::
    $ brownie --network ropsten

Brownie will launch or attach to the client when using any network that includes a ``test-rpc`` dictionary in it's settings.

Each time Brownie is loaded, it will first attempt to connect to the ``host`` address to determine if the RPC client is already active.



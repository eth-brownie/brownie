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

Launching and Connecting to Networks
====================================

Using the CLI
-------------

Brownie will connect to whichever network is set as "default" in ``brownie-config.json``.  

To connect to any other network that has been defined in ``brownie-config.json``, you must specify the `--network` flag when launching Brownie as below:
::
    $ brownie --network ropsten

Brownie will launch or attach to the client when using any network that includes a ``test-rpc`` dictionary in it's settings.

Each time Brownie is loaded, it will first attempt to connect to the ``host`` address to determine if the RPC client is already active.

Using the ``brownie.netowrk`` methods
-------------------------------------

You can interact with any network defined in ``brownie-config.json`` programatically using the ``brownie.network.main`` methods.

Connecting to a network:
.. code-block:: python

    >>> network.connect('ropsten')    
    >>> network.is_connected()
    True
    >>> network.show_active()
    'ropsten'

Disconnecting from a network:
.. code-block:: python

    >>> network.disconnect()
    >>> network.is_connected()
    False

Interacting with  non-local networks
==============================

Accounts
--------

* Configuring accounts for use with non-local networks
When loading an account for interacting with a non-local network, you must provide the private key when loading the account in order to be able to sign transactions or deploy contracts

.. code-block:: python

        >>> accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')
        <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>
        >>> accounts[0].balance()
        17722750299000000000

Once an account is added to the account object, the ``accounts.save`` and ``accounts.load`` can be used to save the accounts to an encrypted keystore and then load for later use.

* Unconfirmed transactions
On non-local networks, blocks are not mined automatically so transaction confirmations will not be immediate.  Transaction receipts are provided immediately can be stored to unique variables.  Individual transaction objects can also be accessed using the ``history`` function.  

Contracts
---------

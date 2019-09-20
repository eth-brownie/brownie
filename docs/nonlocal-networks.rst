.. _nonlocal-networks:

====================
Using Non-Local Networks
====================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can also connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

Warning
========================
Before you go any further, consider that connecting to non-local networks can potentially expose your private keys if you aren't careful.

* When you are interacting with mainnet, make sure you verify all of the details of any transactions you sign/send before you send them. Brownie can't protect you from sending ETH to the wrong address, sending too much, etc. 
* Always protect your private keys.  Don't leave them lying around unencrypted!

Register with Infura
========================
In order to connect to a non-local network you need access to an Ethereum node that supports the JSON RPC.  `Infura <https://infura.io>`__ is one such option.  Once you register and create a project, Infura will provide you with a project ID that can be leveraged to access the given network.

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

Interacting with non-local networks
==============================

``brownie.module.rpc``
--------

The :ref:`rpc` module is unavailable when working with non-local networks.

Accounts
--------

When loading an account for interacting with a non-local network, you must provide the private key when loading the account in order to be able to sign transactions or deploy contracts

.. code-block:: python

        >>> accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')
        <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>
        >>> accounts[0].balance()
        17722750299000000000

Once an account is added to the account object, the ``accounts.save`` and ``accounts.load`` can be used to save the accounts to an encrypted keystore and then load for later use.

Transactions
------------

* Transaction status
When submitting a transaction on non-local networks, blocks are not immediately so transactions will likewise not be immediately confirmed. 
A :ref:`api-network-tx` object is provided immediately and can be stored to unique variables though ``TransactionReceipt.status`` will be ``-1`` until the transaction is mined and either succeeds or reverts.  

* Debugging 
The Brownie :ref:`debug` tools rely upon `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`__ RPC method which is not supported by `Infura <https://infura.io>`__. Attempts to call it will result in a ``RPCRequestError``.
This means that the below ``TransactionReceipt`` attributes and methods are unavailable:

* ``TransactionReceipt.return_value``
* ``TransactionReceipt.trace``
* ``TransactionReceipt.call_trace``
* ``TransactionReceipt.traceback``
* ``TransactionReceipt.source``

:ref:`api-network-contract`
---------
On non-local networks, use the ``Contract`` class to interact with deployed contracts.  ``ContractContainer`` and ``ProjectContract`` are unavailable as these are only used with the local   

You can instantiate the contract using ``contract.Contract`` method.  You will need to provide an ABI (typically as a JSON file) that is generated from the compiled contract code.  

.. code-block:: python

    >>> Contract('0x79447c97b6543F6eFBC91613C655977806CB18b0', "Token", abi)
    <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

Once instantiated, any of the ``Contract``, :ref:`api-contract-call`, or :ref:`api-contract-tx` attributes and methods can be used to interact with the contract.

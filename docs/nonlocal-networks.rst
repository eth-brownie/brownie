.. _nonlocal-networks:

====================
Non-local Networks
====================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can also connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

Warning
========================
Before you go any farther, consider that connecting to non-local networks can potentially expose your private keys if you aren't careful.

* When you are interacting with mainnet, make sure you verify all of the details of any transactions you sign/send before you send them. Brownie can't protect you from sending ETH to the wrong address, sending too much, etc. 
* Always protect your private keys.  Don't leave them lying around unencrypted!

Register with Infura
========================
Before you can connect to a non-local network, you need access to an Ethereum node (whether your own local one or hosted) that supports JSON RPC (either HTTP, IPC, or web-sockets).  `Infura <https://infura.io>`__ is a good option for accessing a hosted node.  Once you register and create a project, Infura will provide you URLs with the API key that can be leveraged to access the given network.

Non-local Network Configuration
================================

Configuring non-local networks
------------------------------

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

You can also set your Infura API key as an environment variable from the command line as below.  
::
    $ export WEB3_INFURA_PROJECT_ID=YourProjectID

Setting the default nerwork
---------------------------

Brownie''s default configuration uses the environment variable WEB3_INFURA_PROJECT_ID.

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

If you are connected to your own private node, Brownie will automatically load any unlocked accounts returned by your node.  In this case, there is no need to use ``accounts.load``.

When interacting with a non-local network via a hosted node like Infura, you must provide the private key when loading your acccount in order to be able to sign transactions or deploy contracts

.. code-block:: python

        >>> accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')
        <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>
        >>> accounts[0].balance()
        17722750299000000000

Once an account is added to the account object, the ``accounts.save`` and ``accounts.load`` can be used to save the accounts to an encrypted keystore and then load for later use.

Transactions
------------

* Transaction status
When submitting transactions on non-local networks, blocks are not immediately so transactions will likewise not be immediately confirmed. 
Brownie does not provide a transaction receipt by default but will wait until the transaction has been confirmed before continuing execution.  
Press ``Ctrl-C`` and a :ref:`api-network-tx` object will be returned with the pending transaction hash and can be stored to unique variables. ``TransactionReceipt.status`` will be ``-1`` until the transaction is mined and either succeeds or reverts.  

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
Contracts
*********

On non-local networks, use the ``Contract`` class to interact with already deployed contracts.  


You can instantiate the contract using ``contract.Contract`` method.  You will need to provide an ABI (typically as a JSON file) that is generated from the compiled contract code.  

.. code-block:: python

    >>> Contract('0x79447c97b6543F6eFBC91613C655977806CB18b0', "Token", abi)
    <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

Once instantiated, any of the ``Contract``, :ref:`api-contract-call`, or :ref:`api-contract-tx` attributes and methods can be used to interact with the contract.

ProjectContract
***************
If you use Brownie to deploy a contract to a non-local network as part of an active project, you can use the :ref:`api-network-contractcontainer`'s ``ContractContainer.at`` method to instantiate a ``ProjectContract`` instance.  Once instantiated, any of the ``Contract`` methods can be used 
.. _nonlocal-networks:

========================
Using Non-Local Networks
========================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

.. warning::

    Before you go any further, consider that connecting to non-local networks can potentially expose your private keys if you aren't careful:

    * When interacting with the mainnet, make sure you verify all of the details of any transactions before signing or sending. Brownie cannot protect you from sending ETH to the wrong address, sending too much, etc.
    * Always protect your private keys. Don't leave them lying around unencrypted!

Registering with Infura
=======================

Before you can connect to a non-local network, you need access to an Ethereum node (whether your own local one or hosted) that supports JSON RPC (either HTTP, IPC, or web-sockets). `Infura <https://infura.io>`_ is a good option for accessing a hosted node. Once you register and create a project, Infura will provide you with a project ID as well as API URLs that can be leveraged to access the given network.

Network Configuration
=====================

Defining Non-Local Networks
---------------------------

The connection settings for non-local networks must be defined in ``brownie-config.yaml``.

First, for each network you want to configure, create a new section in the network.networks section as below:

.. code-block:: yaml

    network:
        networks:
            ropsten:
                host: http://ropsten.infura.io/v3/$WEB3_INFURA_PROJECT_ID

If using Infura, you can provide your project ID key as an environment variable or by modifying the ``hosts`` setting in the configuration file.

The environment variable is set to ``WEB3_INFURA_PROJECT_ID`` in the default configuration file. Use the following command to set the environment variable:

::

    $ export WEB3_INFURA_PROJECT_ID=YourProjectID

Setting the Default Network
---------------------------

To modify the default network that Brownie connects to, update the network.default field as shown below:

.. code-block:: yaml

    network:
        default: ropsten

Launching and Connecting to Networks
====================================

Using the CLI
-------------

By default, Brownie will connect to whichever network is set as "default" in ``brownie-config.yaml``. To connect to a different network, use the ``--network`` flag:

::

    $ brownie --network ropsten


Using brownie.network
---------------------

The ``brownie.network`` module conains methods that allow you to connect or disconnect from any network defined within the configuration file.

To connect to a network:

.. code-block:: python

    >>> network.connect('ropsten')
    >>> network.is_connected()
    True
    >>> network.show_active()
    'ropsten'

To disconnect:

.. code-block:: python

    >>> network.disconnect()
    >>> network.is_connected()
    False

.. _nonlocal-networks-interacting:

Interacting with Non-Local Networks
===================================

There are several key differences in functionality between using a non-local network as opposed to a local develpment environment.

Contracts
---------

.. _nonlocal-networks-contracts:

ProjectContract
***************

By default, Brownie stores information about contract deployments on non-local networks. ``ProjectContract`` instances will persist through the following actions:

* Disconnecting and reconnecting to the same network
* Closing and reloading a project
* Exiting and reloading Brownie
* Modifying a contract's source code - Brownie still retains the source for the deployed version

The following actions will remove locally stored data for a ``ProjectContract``:

* Calling ``ContractContainer.remove`` or ``ContractContainer.clear`` will erase deployment information for the removed ``ProjectContract`` instances.
* Removing a contract source file from your project (or renaming it) will cause Brownie to delete all deployment information for the removed contract.

You can create a ``ProjectContract`` instance for an already-deployed contract with the :ref:`api-network-contractcontainer`'s ``ContractContainer.at`` method.

See :ref:`config` for information on how to enable or disable persistence.

Contract
********

The :ref:`Contract<api-network-contract>` class (available as ``brownie.Contract``) is used to interact with already deployed contracts that are not a part of your core project. You will need to provide an ABI as a ``dict`` generated from the compiled contract code.

.. code-block:: python

    >>> Contract('0x79447c97b6543F6eFBC91613C655977806CB18b0', "Token", abi)
    <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

Once instantiated, all of the usual ``Contract`` attributes and methods can be used to interact with the deployed contract.

.. _nonlocal-networks-accounts:

Accounts
--------

Brownie will automatically load any unlocked accounts returned by a node. If you are using your own private node, you will be able to access your accounts in the same way you would in a local environment.

When connected to a hosted node such as Infura, local accounts must be added via the ``Accounts.add`` method:

.. code-block:: python

    >>> accounts.add('8fa2fdfb89003176a16b707fc860d0881da0d1d8248af210df12d37860996fb2')
    <Account object '0xc1826925377b4103cC92DeeCDF6F96A03142F37a'>
    >>> accounts[0].balance()
    17722750299000000000

Once an account is added to the ``Accounts`` object, use :ref:`Account.save <api-network-accounts-load>` to save the it to an encrypted keystore, and :ref:`Accounts.load <api-network-accounts-load>` to open it for subsequent use.

Transactions
------------

After broadcasting a transaction, Brownie will pause and wait until it confirms. If you are using the console you can press ``Ctrl-C`` to immediately receive the :ref:`api-network-tx` object. Note that ``TransactionReceipt.status`` will be ``-1`` until the transaction is mined, and many attributes and methods will not yet be available.

Debugging
*********

Brownie's :ref:`debugging tools<debug>` rely upon the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`__ RPC method which is not supported by Infura. Attempts to call it will result in a ``RPCRequestError``. This means that the following ``TransactionReceipt`` attributes and methods are unavailable:

* ``TransactionReceipt.return_value``
* ``TransactionReceipt.trace``
* ``TransactionReceipt.call_trace``
* ``TransactionReceipt.traceback``
* ``TransactionReceipt.source``

Rpc
---

The :ref:`rpc` object is unavailable when working with non-local networks.

.. _network-management:

==================
Network Management
==================

Brownie can be used with both development and live environments.

    * A **development** environment is a local, temporary network used for testing and debugging. Brownie uses `Ganache <https://github.com/trufflesuite/ganache-cli>`_ for development environments.
    * A **live** environment is a non-local, persistent blockchain. This term is used to refer to both the Ethereum mainnet and testnets.

Network Configuration
=====================

Networks settings are handled using the command-line:

::

    $ brownie networks

Viewing Existing Networks
-------------------------

Networks are broadly categorized as "development" (local, ephemeral environments) and "live" (non-local, persistent environments).  Live networks are additionally categorized by chain (Ethereum, ETC, etc).

Type ``brownie networks list`` to view a list of existing networks:

::

    $ brownie networks list
    Brownie - Python development framework for Ethereum

    The following networks are declared:

    Ethereum
      ├─Mainnet (Infura): mainnet
      ├─Ropsten (Infura): ropsten
      ├─Rinkeby (Infura): rinkeby
      ├─Goerli (Infura): goerli
      └─Kovan (Infura): kovan

    Ethereum Classic
      ├─Mainnet: etc
      └─Kotti: kotti

    Development
      └─Ganache-CLI: development


Adding a New Network
--------------------

To add a new network:

::

    $ brownie networks add [environment] [id] host=[host] [KEY=VALUE, ...]

When declaring a new network, the following fields must always be included:

    * ``environment``: the category that the network should be placed in, e.g. "Ethereum", "Ethereum Classic", or "Development"
    * ``id``: a unique identifier for the network, e.g. "mainnet"
    * ``host``: the address of the node to connect to, e.g. ``https://mainnet.infura.io/v3/1234567890abcdef``

The following fields are optional:

    * ``name`` A longer name to use for the network. If not given, ``id`` is used.

There are additional required and optional fields that are dependent on the type of network.

Live Networks
*************

Live networks **must** include the following fields:

    * ``chainid``: The chain ID for a network. Live networks with the same chain ID share local data about :ref:`contract deployments <core-contracts-live>`. See `chainid.network <https://chainid.network/>`_ for a list of chain IDs.

The following fields are optional for live networks:

    * ``explorer``: API url used by :func:`Contract.from_explorer <Contract.from_explorer>` to fetch source code. If this field is not given, you will not be able to fetch source code when using this network.

Development Networks
********************

Development networks **must** include the following fields:

    * ``cmd``: The command used to launch the local RPC client, e.g. ``ganache-cli``.

The following optional fields may be given for development networks, which are passed into Ganache as commandline arguments:

    * ``port``: The port to connect to. If not given as a unique field, it should be included within the host path.
    * ``gas_limit``: The block gas limit. Defaults to 6721925.
    * ``accounts``: The number of funded, unlocked accounts. Default 10.
    * ``mnemonic``: A mnemonic to use when generating local accounts.
    * ``evm_version``: The EVM ruleset to use. Default is the most recent available.
    * ``fork``: If given, the local client will fork from another currently running Ethereum client at a given block. Input should be the HTTP location and port of the other client, e.g. ``http://localhost:8545`` or optionally provide a block number ``http://localhost:8545@1599200``.

.. note::

    ``brownie networks list true`` shows a detailed view of existing networks, including all configuration fields. This can be useful for defining fields of a new network.

Setting the Default Network
---------------------------

To modify the default network, add the``networks.default`` field to your project configuration file:

.. code-block:: yaml

    networks:
        default: ropsten

If a configuration file does not exist you will have to create one. See the documentation on :ref:`configuration files<config>` for more information.


Launching and Connecting
========================

Using the CLI
-------------

By default, Brownie will launch and connect to ``ganache-cli`` each time it is loaded. To connect to a different network, use the ``--network`` flag with the ID of the network you wish to connect to:

::

    $ brownie --network ropsten

Using brownie.network
---------------------

The :func:`brownie.network <main.connect>` module contains methods that allow you to connect or disconnect from any already-defined network.

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

Live Networks
=============

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ as a local development environment, Brownie can be used on live networks (i.e. any testnet/mainnet node that supports JSON RPC).

.. warning::

    Before you go any further, consider that connecting to a live network can potentially expose your private keys if you aren't careful:

    * When interacting with the mainnet, make sure you verify all of the details of any transactions before signing or sending. Brownie cannot protect you from sending ETH to the wrong address, sending too much, etc.
    * Always protect your private keys. Don't leave them lying around unencrypted!

Personal Node vs Hosted Node
----------------------------

To interact with a live network you must connect to a node. You can either run your own node, or connect to a hosted node.

Running your Own Node
*********************

Clients such as `Geth <https://geth.ethereum.org/>`_ or `Parity <https://www.parity.io/ethereum/>`_ can be used to run your own Ethereum node, that Brownie can then connect to. Having your node gives you complete control over which RPC endpoints are available and ensures you have a private and dedicated connection to the network. Unfortunately, keeping a node operating and synced can be a challenging task.

If you wish to learn more about running a node, ethereum.org provides a `list of resources <https://ethereum.org/developers/#testnets-and-faucets>`_ that you can use to get started.

Using a Hosted Node
*******************

Services such as `Infura <https://infura.io>`_ provide public access to Ethereum nodes. This is a much simpler option than running your own, but it is not without limitations:

    1. Some RPC endpoints may be unavailable. In particular, Infura does not provide access to the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`_ method. For this reason, Brownie's :ref:`debugging tools<debug>` will not work when connected via Infura.
    2. Hosted nodes do not provide access to accounts - this would be a major security hazard! You will have to manually unlock your own :ref:`local account<local-accounts>` before you can make a transaction.

Using Infura
^^^^^^^^^^^^

To Infura you need to `register for an account <https://infura.io/register>`_. Once you have signed up, login and create a new project. You will be provided with a project ID, as well as API URLs that can be leveraged to access the network.

To connect to Infura using Brownie, store your project ID as an environment variable named ``WEB3_INFURA_PROJECT_ID``. You can do so with the following command:

::

    $ export WEB3_INFURA_PROJECT_ID=YourProjectID

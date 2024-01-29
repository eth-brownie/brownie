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
      ├─Ganache-CLI: development
      └─Ganache-CLI (Mainnet Fork): mainnet-fork


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
    * ``timeout``: The number of seconds to wait for a response when making an RPC call. Defaults to 30.

There are additional required and optional fields that are dependent on the type of network.

Live Networks
*************

Live networks **must** include the following fields:

    * ``chainid``: The chain ID for a network. Live networks with the same chain ID share local data about :ref:`contract deployments <core-contracts-live>`. See `chainid.network <https://chainid.network/>`_ for a list of chain IDs.

The following fields are optional for live networks:

    * ``explorer``: API url used by :func:`Contract.from_explorer <Contract.from_explorer>` to fetch source code. If this field is not given, you will not be able to fetch source code when using this network.


.. _adding-network:

Development Networks
********************

Development networks **must** include the following fields:

    * ``cmd``: The command used to launch the local RPC client, e.g. ``ganache-cli``.

The following optional fields may be given for development networks, which are passed into Ganache as commandline arguments:

    * ``port``: The port to connect to. If not given as a unique field, it should be included within the host path.
    * ``gas_limit``: The block gas limit. Defaults to 6721925.
    * ``accounts``: The number of funded, unlocked accounts. Default 10.
    * ``mnemonic``: A mnemonic to use when generating local accounts.
    * ``chain_id``: The chain id as integer used for ``eth_chainId`` and the ``CHAINID`` opcode. If no value is given, defaults to the chain id of the forked network or to 1337 and 1 respectively if no fork is specified.
    * ``network_id``: The network id as integer used by ganache to identify itself. Defaults to the current timestamp or the network id of the forked chain.
    * ``evm_version``: The EVM ruleset to use. Default is the most recent available.
    * ``fork``: If given, the local client will fork from another currently running Ethereum client. The value may be an HTTP location and port of the other client, e.g. ``http://localhost:8545``, or the ID of a production network, e.g. ``mainnet``. See :ref:`Using a Forked Development Network <network-management-fork>`.
    * ``disable_cache``: If true, disables caching of all forking requests.
    * ``block_time``: The time waited between mining blocks. Defaults to instant mining.
    * ``default_balance``: The starting balance for all unlocked accounts. Can be given as unit string like "1000 ether" or "50 gwei" or as an number **in Ether**. Will default to 100 ether.
    * ``time``: Date (ISO 8601) that the first block should start. Use this feature, along with :func:`Chain.sleep <Chain.sleep>` to test time-dependent code. Defaults to the current time.
    * ``unlock``: A single address or a list of addresses to unlock. These accounts are added to the :func:`Accounts <brownie.network.account.Accounts>` container and can be used as if the private key is known. Also works in combination with ``fork`` to send transactions from any account.
    * ``unlimited_contract_size``: Allows deployed contracts to be over the maximum limit of 24675 bytes. The value should be either `true` or `false`.

.. note::
    These optional commandline fields can also be specified on a project level in the project's ``brownie-config.yaml`` file. See the :ref:`configuration files<config>`.

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

.. _network-management-live:

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

If you wish to learn more about running a node, ethereum.org provides a `list of resources <https://ethereum.org/en/developers/docs/nodes-and-clients/>`_ that you can use to get started.

Using a Hosted Node / Providers
========================================

Services such as `Alchemy <https://www.alchemy.com>`_ and `Infura <https://infura.io>`_ provide public access to Ethereum nodes. This is a much simpler option than running your own, but it is not without limitations:

    1. Some RPC endpoints may be unavailable. In particular, Infura does not provide access to the `debug_traceTransaction <https://geth.ethereum.org/docs/rpc/ns-debug#debug_tracetransaction>`_ method. For this reason, Brownie's :ref:`debugging tools<debug>` will not work when connected via Infura.
    2. Hosted nodes do not provide access to accounts - this would be a major security hazard! You will have to manually unlock your own :ref:`local account<local-accounts>` before you can make a transaction.

Brownie allows you to bulk modify the provider you use by setting the `provider` field in the networks, and the associated provider.

::

    $ brownie networks list_providers

    Brownie v1.17.2 - Python development framework for Ethereum

    The following providers are declared:
    ├─dict_keys(['infura', 'alchemy']):

or

::

    $ brownie networks list_providers True

    Brownie v1.17.2 - Python development framework for Ethereum

    The following providers are declared:
    ├─provider: infura:
    ├─   host: {'host': 'https://{}.infura.io/v3/$WEB3_INFURA_PROJECT_ID'}:
    ├─provider: alchemy:
    ├─   host: {'host': 'https://eth-{}.alchemyapi.io/v2/$WEB3_ALCHEMY_PROJECT_ID'}:


Any `network` that has a `provider` set will be able to be swapped to the format of another provider. For example, to swap all provider-based networks to Alchemy, run:

::

    $ brownie networks set_provider alchemy


And it'll print out all the valid networks to swap to the Alchemy format. If you don't have a `provider` set, you can set one with:

::

    $ brownie networks modify mainnet provider=alchemy


Adding Providers
----------------

To add or update a provider, run:

::

    $ brownie networks update_provider alchemy https://eth-{}.alchemyapi.io/v2/$WEB3_ALCHEMY_PROJECT_ID


This URL will allow brownie to swap out the {} with whatever network it's on, and you'll set a `WEB3_ALCHEMY_PROJECT_ID` environment variable as your Alchemy key.

Using Infura
************

To Infura you need to `register for an account <https://infura.io/register>`_. Once you have signed up, login and create a new project. You will be provided with a project ID, as well as API URLs that can be leveraged to access the network.

To connect to Infura using Brownie, store your project ID as an environment variable named ``WEB3_INFURA_PROJECT_ID``. You can do so with the following command:

::

    $ export WEB3_INFURA_PROJECT_ID=YourProjectID

Or adding `export WEB3_INFURA_PROJECT_ID=YourProjectID` to your `.env` and adding `dotenv: .env` to your `brownie-config.yaml`.


Using Alchemy
*************

To Alchemy you need to `signup for an account <https://auth.alchemyapi.io/signup>`_. Once you have signed up, login and create a new project. You will be provided with a URL that can be leveraged to access the network.

Hit the `view key` button, and you'll be given a URL. You can just use the section after the last slash as your `WEB3_ALCHEMY_PROJECT_ID`. For example if your full key is: `https://eth-mainnet.alchemyapi.io/v2/1234`, your `WEB3_ALCHEMY_PROJECT_ID` would be `1234`.
Note, this only works well with ETH networks at the moment, but you can modify your providers list at any time.

You can set your `WEB3_ALCHEMY_PROJECT_ID` with the following command
::

    $ export WEB3_ALCHEMY_PROJECT_ID=YourProjectID

Or adding `export WEB3_ALCHEMY_PROJECT_ID=YourProjectID` to your `.env` and adding `dotenv: .env` to your `brownie-config.yaml`.

To connect with other non-ethereum networks through alchemy, you'll have to follow the normal network adding process.

.. _network-management-fork:

Using a Forked Development Network
==================================

Ganache allows you create a development network by forking from an live network. This is useful for testing interactions between your project and other projects that are deployed on the main-net.

Brownie's ``mainnet-fork`` network uses Infura to create a development network that forks from the main-net. To connect with the console:

::

    $ brownie console --network mainnet-fork

In this mode, you can use :func:`Contract.from_explorer <Contract.from_explorer>` to fetch sources and interact with contracts on the network you have forked from.

.. note::

    Forking from Infura can be *very slow*. If you are using this mode
    extensively, it may be useful to run your own Geth node.

Native EVM-Compatible Chain Integrations
========================================

Brownie natively supports the following collection of EVM-compatible chains:

* Ethereum Classic
* Arbitrum
* Avalanche
* Aurora
* Binance Smart Chain
* Boba
* Fantom Opera
* Harmony
* Hedera
* Moonbeam
* Moonriver
* Optimistic Ethereum
* Polygon Network
* Gnosis Network

In order to enable native support for an EVM-compatible chain, there are 2 requirements. The chain must have a JSON-RPC endpoint which is publicly accessible (free in cost, sign-up may be required), and it should have a block explorer with API support for fetching contract sources and ABIs.

.. note::

    Although an EVM-compatible chain/network may not be natively supported, it can still be manually added to the local network list for developing on. See :ref:`Adding a New Network`

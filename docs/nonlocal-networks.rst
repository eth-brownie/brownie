.. _nonlocal-networks:

========================
Using Non-Local Networks
========================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ as a local development environment, Brownie can connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

.. warning::

    Before you go any further, consider that connecting to non-local networks can potentially expose your private keys if you aren't careful:

    * When interacting with the mainnet, make sure you verify all of the details of any transactions before signing or sending. Brownie cannot protect you from sending ETH to the wrong address, sending too much, etc.
    * Always protect your private keys. Don't leave them lying around unencrypted!

Personal Node vs Hosted Node
============================

In order to interact with a non-local network you must connect to a node. You can either run your own node, or connect to a hosted node.

Running your Own Node
---------------------

Clients such as `Geth <https://geth.ethereum.org/>`_ or `Parity <https://www.parity.io/ethereum/>`_ can be used to run your own Ethereum node, that Brownie can then connect to. Having your node gives you complete control over which RPC endpoints are available and ensures you have a private and dedicated connection to the network. Unfortunately, keeping a node operating and synced can be a challenging task.

If you wish to learn more about running a node, ethereum.org provides a `list of resources <https://ethereum.org/developers/#testnets-and-faucets>`_ that you can use to get started.

Using a Hosted Node
-------------------

Services such as `Infura <https://infura.io>`_ provide public access to Ethereum nodes. This is a much simpler option than running your own, but it is not without limitations:

    1. Some RPC endpoints may be unavailable. In particular, Infura does not provide access to the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`_ method. For this reason, Brownie's :ref:`debugging tools<debug>` will not work when connected via Infura.
    2. Hosted nodes do not provide access to accounts - this would be a major security hazard! You will have to manually unlock your own :ref:`local account<local-accounts>` before you can make a transaction.

Using Infura
************

Before you can onnect to Infura you need to `register for an account <https://infura.io/register>`_. After you have signed up, login and create a new project. You will be provided with a project ID, as well as API URLs that can be leveraged to access the network.

To connect to Infura using Brownie, store your project ID as an environment variable named ``WEB3_INFURA_PROJECT_ID``. You can do so with the following command:

::

    $ export WEB3_INFURA_PROJECT_ID=YourProjectID

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

The :func:`brownie.network <main.connect>` module conains methods that allow you to connect or disconnect from any network defined within the configuration file.

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

.. _nonlocal-networks:

====================
Non-local Networks
====================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can also connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

Warning
========================
Before you go any farther, consider that connecting to non-local networks can potentially open you up to several risks, including the below:
* When you are interacting with mainnet, make sure you verify all of the details of any transactions you sign/send before you send them.  
* Always protect your private keys.  Don't leave them lying around unencrypted!

Register with Infura
========================
Before you can connect to a non-local network, you need access to a remote Ethereum node that supports JSON RPC over HTTP.  `Infura <https://infura.io>`__ is one such option.  Once you register and create a project, Infura will provide you URLs with the API key that can be leveraged to access the given network.

Non-local Network Configuration
========================

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

By default, Brownie will connect to the local network run by `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__.  To connect to a non-local network, you must specify the `--network` flag when launching Brownie. 

Brownie will launch or attach to the client when using any network that includes a ``test-rpc`` dictionary in it's settings.

Each time Brownie is loaded, it will first attempt to connect to the ``host`` address to determine if the RPC client is already active.

Client is Active
----------------

If able to connect to the ``host`` address, Brownie:

* Checks the current block height and raises an Exception if it is greater than zero
* Locates the process listening at the address and attaches it to the ``Rpc`` object
* Takes a snapshot

When Brownie is terminated:

* The RPC client is reverted based on the initial snapshot.

Client is not Active
--------------------

If unable to connect to the ``host`` address, Brownie:

* Launches the client using the ``test-rpc`` command given in the configuration file
* Waits to see that the process loads successfully
* Confirms that it can connect to the new process
* Attaches the process to the ``Rpc`` object

When Brownie is terminated:

* The RPC client and any child processes are also terminated.

Common Interactions
===================

You can interact with the RPC client using the :ref:`rpc` object, which is automatically instantiated as ``rpc``:

.. code-block:: python

    >>> rpc
    <brownie.network.rpc.Rpc object at 0x7f720f65fd68>

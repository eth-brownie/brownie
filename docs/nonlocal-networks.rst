.. _nonlocal-networks:

====================
Non-local Networks
====================

In addition to using `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment, Brownie can also connect to non-local networks (i.e. any testnet/mainnet node that supports JSON RPC).

Warning
========================
Before you go any farther, consider that connecting to non-local networks can potentially open you up to several risks, including the below:
* Brownie is a testing framework and not designed for interactions with any mainnet (Ethereum, xDai, POA, etc.) and has not been audited for any security risks
* Brownie should not be used to sign or send transactions to any mainnet or real value can potentially be lost.
* If you use an account where you have real value stored on any mainnet, you should not use that account when interacting with Brownie

Non-local Network Configuration
========================

The connection settings for non-local networks must be defined in ``brownie-config.json``:

.. code-block:: javascript

    "development": {
        "test-rpc": {
            "cmd": "ganache-cli", // command to load the client - you can add any extra flags here as needed
            "port": 8545,  // port the client should listen on
            "gas_limit": 6721975,  // block gas limit
            "accounts": 10,  // number of accounts in web3.eth.accounts
            "evm_version": "petersburg",  // evm version
            "mnemonic": "brownie"  // accounts are derived from this mnemonic - set to null for different addresses on each load
        },
        "host": "http://ropsten.infura.io/v3/[yourInfuraApiKey]"
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

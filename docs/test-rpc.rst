.. _test-rpc:

====================
The Local RPC Client
====================

Brownie is designed to use `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment.

Launching and Connecting
========================

The connection settings for the local RPC are outlined in ``brownie-config.json``:

.. code-block:: javascript

    "development": {
        "test-rpc": "ganache-cli",
        "host": "http://127.0.0.1:8545"
    }

Each time Brownie is loaded, it will first attempt to connect to the ``host`` address to determine if the RPC client is already active.

RPC Client is Active
---------------------

If able to connect to the ``host`` address, Brownie:
If Brownie is able to connect at the ``host`` address, the following actions happen during launch:

* Checks the current block height and raises an Exception if it is greater than zero
* Locates the process listening at the address and attaches it to the ``Rpc`` object
* Takes a snapshot

When Brownie is terminated:

* The RPC client is reverted based on the initial snapshot.

RPC Client is not Active
------------------------

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

Mining
------

To mine empty blocks, use ``rpc.mine``.

.. code-block:: python

    >>> web3.eth.blockNumber
    0
    >>> rpc.mine(50)
    Block height at 50
    >>> web3.eth.blockNumber
    50

Time
----

You can call ``rpc.time`` to view the current epoch time. To fast forward, call ``rpc.sleep``.

.. code-block:: python

    >>> rpc.time()
    1557151189
    >>> rpc.sleep(100)
    >>> rpc.time()
    1557151289

Snapshots
---------

``rpc.snapshot`` takes a snapshot of the current state of the blockchain. You can return to this state later using ``rpc.revert``.

.. code-block:: python

    >>> rpc.snapshot()
    Snapshot taken at block height 4
    >>> accounts[0].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca
    Transaction confirmed - block: 5   gas used: 21000 (100.00%)
    <Transaction object '0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca'>
    >>> accounts[0].balance()
    89999580000000000000
    >>> rpc.revert()
    Block height reverted to 4
    >>> accounts[0].balance()
    100000000000000000000

To return to the genesis state, use ``rpc.reset``.

.. code-block:: python

    >>> web3.eth.blockNumber
    6
    >>> rpc.reset()
    >>> web3.eth.blockNumber
    0

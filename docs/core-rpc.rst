.. _core-rpc:

==========================
The Local Test Environment
==========================

Brownie is designed to use `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ as a local development environment. Functionality such as snapshotting and time travel is accessible via the :func:`Rpc <brownie.network.rpc.Rpc>` object, available as ``rpc``:

.. code-block:: python

    >>> rpc
    <brownie.network.rpc.Rpc object at 0x7f720f65fd68>

Mining
------

Ganache mines a new block each time you broadcast a transaction. You can mine empty blocks with the :func:`rpc.mine <Rpc.mine>` method.

.. code-block:: python

    >>> web3.eth.blockNumber
    0
    >>> rpc.mine(50)
    Block height at 50
    >>> web3.eth.blockNumber
    50

Time
----

You can call :func:`rpc.time <Rpc.time>` to view the current epoch time. To fast forward, call :func:`rpc.sleep <Rpc.sleep>`.

.. code-block:: python

    >>> rpc.time()
    1557151189
    >>> rpc.sleep(100)
    >>> rpc.time()
    1557151289

Snapshots
---------

Use :func:`rpc.snapshot <Rpc.snapshot>` to take a snapshot of the current state of the blockchain:

.. code-block:: python

    >>> rpc.snapshot()
    Snapshot taken at block height 4
    >>> accounts[0].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca
    Transaction confirmed - block: 5   gas used: 21000 (100.00%)
    <Transaction object '0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca'>

You can then return to this state later using :func:`rpc.revert <Rpc.revert>`:

.. code-block:: python

    >>> accounts[0].balance()
    89999580000000000000
    >>> rpc.revert()
    Block height reverted to 4
    >>> accounts[0].balance()
    100000000000000000000

Reverting does not consume the snapshot; you can return to the same snapshot as many times as needed. However, if you take a new snapshot the previous one is no longer accessible.

To return to the genesis state, use :func:`rpc.reset <Rpc.reset>`.

.. code-block:: python

    >>> web3.eth.blockNumber
    6
    >>> rpc.reset()
    >>> web3.eth.blockNumber
    0

Undo / Redo
-----------

Along with snapshotting, you can use :func:`rpc.undo <Rpc.undo>` and :func:`rpc.redo <Rpc.redo>` to move backward and forward through recent transactions. This is especially useful during :ref:`interactive test debugging <pytest-interactive>`.

.. code-block:: python

    >>> accounts[0].transfer(accounts[1], "1 ether")
    Transaction sent: 0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05
      Gas price: 0.0 gwei   Gas limit: 6721975
      Transaction confirmed - Block: 1   Gas used: 21000 (0.31%)

    <Transaction '0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05'>

    >>> rpc.undo()
    'Block height at 0'

    >>> rpc.redo()
    Transaction sent: 0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05
      Gas price: 0.0 gwei   Gas limit: 6721975
      Transaction confirmed - Block: 1   Gas used: 21000 (0.31%)

    'Block height at 1'

Note that :func:`rpc.snapshot <Rpc.snapshot>` and :func:`rpc.revert <Rpc.revert>` clear the undo buffer.

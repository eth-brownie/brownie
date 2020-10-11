.. _core-chain:

===============================
Interacting with the Blockchain
===============================

Accessing Block Information
===========================

The :func:`Chain <brownie.network.state.Chain>` object, available as ``chain``, uses list-like syntax to provide access to block information:

.. code-block:: python

    >>> chain
    <Chain object (chainid=1, height=10451202)>

    >>> chain[2000000]
    AttributeDict({
        'difficulty': 49824742724615,
        'extraData': '0xe4b883e5bda9e7a59ee4bb99e9b1bc',
        'gasLimit': 4712388,
        'gasUsed': 21000,
        'hash': '0xc0f4906fea23cf6f3cce98cb44e8e1449e455b28d684dfa9ff65426495584de6',
        'logsBloom': '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
        'miner': '0x61c808d82a3ac53231750dadc13c777b59310bd9',
        'nonce': '0x3b05c6d5524209f1',
        'number': 2000000,
        'parentHash': '0x57ebf07eb9ed1137d41447020a25e51d30a0c272b5896571499c82c33ecb7288',
        'receiptRoot': '0x84aea4a7aad5c5899bd5cfc7f309cc379009d30179316a2a7baa4a2ea4a438ac',
        'sha3Uncles': '0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347',
        'size': 650,
        'stateRoot': '0x96dbad955b166f5119793815c36f11ffa909859bbfeb64b735cca37cbf10bef1',
        'timestamp': 1470173578,
        'totalDifficulty': 44010101827705409388,
        'transactions': ['0xc55e2b90168af6972193c1f86fa4d7d7b31a29c156665d15b9cd48618b5177ef'],
        'transactionsRoot': '0xb31f174d27b99cdae8e746bd138a01ce60d8dd7b224f7c60845914def05ecc58',
        'uncles': [],
    })

    >>> web3.eth.blockNumber
    10451202

    >>> len(chain)
    10451203  # always +1 to the current block number, because the first block is zero

    >>> chain[0] == web3.eth.getBlock(0)
    True

    # for negative index values, the block returned is relative to the most recently mined block
    >>> chain[-1] == web3.eth.getBlock('latest')
    True

Accessing Transaction Data
==========================

Local Transaction History
-------------------------

The :func:`TxHistory <brownie.network.state.TxHistory>` container, available as ``history``, holds all the transactions that have been broadcasted during the Brownie session. You can use it to access :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects if you did not assign them to a variable when making the call.

.. code-block:: python

    >>> history
    [
        <Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>,
        <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>
    ]

You can use :func:`history.filter <TxHistory.filter>` to filter for specific transactions, either with key-value pairs or a lambda function:

.. code-block:: python

    >>> history.filter(sender=accounts[0], value="1 ether")
    [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>]

    >>> history.filter(key=lambda k: k.nonce < 2)
    [<Transaction '0x03569ee152b04ba5b55c2bf05f99f7ec153db715acfe0c1600f144ded58f31fe'>, <Transaction '0x42193c0ff7007c6e2a5e5572a3c6b5706cd133d21e30e5826add3d971134504c'>]

Other Transactions
------------------

Use :func:`chain.get_transaction <Chain.get_transaction>` to get a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object for any transaction:

.. code-block:: python

    >>> chain.get_transaction('0xf598d43ef34a48478f3bb0ad969c6735f416902c4eb1eb18ebebe0fca786105e')
    <Transaction '0xf598d43ef34a48478f3bb0ad969c6735f416902c4eb1eb18ebebe0fca786105e'>

This also works for pending transactions. When the transaction has not yet confirmed, the transaction hash is displayed in yellow within the console.

Manipulating the Development Chain
==================================

Brownie is designed to use `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ as a local development environment. Functionality such as mining, snapshotting and time travel is accessible via the :func:`Chain <brownie.network.state.Chain>` object.

Mining New Blocks
-----------------

Ganache's default behavior is to mine a new block each time you broadcast a transaction. You can mine empty blocks with the :func:`chain.mine <Chain.mine>` method:

.. code-block:: python

    >>> web3.eth.blockNumber
    0
    >>> chain.mine(50)
    50
    >>> web3.eth.blockNumber
    50

Time Travel
-----------

You can call :func:`chain.time <Chain.time>` to view the current epoch time. To fast forward the clock, call :func:`chain.sleep <Chain.sleep>`.

.. code-block:: python

    >>> chain.time()
    1500000000
    >>> chain.sleep(31337)
    >>> chain.time()
    1500031337

Snapshots
---------

Use :func:`chain.snapshot <Chain.snapshot>` to take a snapshot of the current state of the blockchain:

.. code-block:: python

    >>> chain.snapshot()

    >>> accounts[0].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca
    Transaction confirmed - block: 5   gas used: 21000 (100.00%)
    <Transaction object '0xd5d3b40eb298dfc48721807935eda48d03916a3f48b51f20bcded372113e1dca'>

You can then return to this state later using :func:`chain.revert <Chain.revert>`:

.. code-block:: python

    >>> accounts[0].balance()
    89999580000000000000
    >>> chain.revert()
    4
    >>> accounts[0].balance()
    100000000000000000000

Reverting does not consume the snapshot; you can return to the same snapshot as many times as needed. However, if you take a new snapshot the previous one is no longer accessible.

To return to the genesis state, use :func:`chain.reset <Chain.reset>`.

.. code-block:: python

    >>> web3.eth.blockNumber
    6
    >>> chain.reset()
    >>> web3.eth.blockNumber
    0

Undo / Redo
-----------

Along with snapshotting, you can use :func:`chain.undo <Chain.undo>` and :func:`chain.redo <Chain.redo>` to move backward and forward through recent transactions. This is especially useful during :ref:`interactive test debugging <pytest-interactive>`.

.. code-block:: python

    >>> accounts[0].transfer(accounts[1], "1 ether")
    Transaction sent: 0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05
      Gas price: 0.0 gwei   Gas limit: 6721975
      Transaction confirmed - Block: 1   Gas used: 21000 (0.31%)

    <Transaction '0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05'>

    >>> chain.undo()
    0

    >>> chain.redo()
    Transaction sent: 0x8c166b66b356ad7f5c58337973b89950f03105cdae896ac66f16cdd4fc395d05
      Gas price: 0.0 gwei   Gas limit: 6721975
      Transaction confirmed - Block: 1   Gas used: 21000 (0.31%)


Note that :func:`chain.snapshot <Chain.snapshot>` and :func:`chain.revert <Chain.revert>` clear the undo buffer.

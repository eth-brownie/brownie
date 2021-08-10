.. _core-chain:

===============================
Interacting with the Blockchain
===============================

Accessing Block Information
===========================

The :func:`Chain <brownie.network.state.Chain>` object, available as ``chain``, uses list-like syntax to provide access to block information:

.. code-block:: python

    >>> chain
    <Chain object (chainid=1, height=12965000)>

    >>> chain[12965000]
    AttributeDict({
        'baseFeePerGas': 1000000000,
        'difficulty': 7742494561645080,
        'extraData': HexBytes('0x68747470733a2f2f7777772e6b7279707465782e6f7267'),
        'gasLimit': 30029122,
        'gasUsed': 30025257,
        'hash': HexBytes('0x9b83c12c69edb74f6c8dd5d052765c1adf940e320bd1291696e6fa07829eee71'),
        'logsBloom': HexBytes('0x24e74ad77d9a2b27bdb8f6d6f7f1cffdd8cfb47fdebd433f011f7dfcfbb7db638fadd5ff66ed134ede2879ce61149797fbcdf7b74f6b7de153ec61bdaffeeb7b59c3ed771a2fe9eaed8ac70e335e63ff2bfe239eaff8f94ca642fdf7ee5537965be99a440f53d2ce057dbf9932be9a7b9a82ffdffe4eeee1a66c4cfb99fe4540fbff936f97dde9f6bfd9f8cefda2fc174d23dfdb7d6f7dfef5f754fe6a7eec92efdbff779b5feff3beafebd7fd6e973afebe4f5d86f3aafb1f73bf1e1d0cdd796d89827edeffe8fb6ae6d7bf639ec5f5ff4c32f31f6b525b676c7cdf5e5c75bfd5b7bd1928b6f43aac7fa0f6336576e5f7b7dfb9e8ebbe6f6efe2f9dfe8b3f56'),
        'miner': '0x7777788200B672A42421017F65EDE4Fc759564C8',
        'mixHash': HexBytes('0x9620b46a81a4795cf4449d48e3270419f58b09293a5421205f88179b563f815a'),
        'nonce': HexBytes('0xb223da049adf2216'),
        'number': 12965000,
        'parentHash': HexBytes('0x3de6bb3849a138e6ab0b83a3a00dc7433f1e83f7fd488e4bba78f2fe2631a633'),
        'receiptsRoot': HexBytes('0x8a8865cd785e2e9dfce7da83aca010b10b9af2abbd367114b236f149534c821d'),
        'sha3Uncles': HexBytes('0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347'),
        'size': 137049,
        'stateRoot': HexBytes('0x41cf6e8e60fd087d2b00360dc29e5bfb21959bce1f4c242fd1ad7c4da968eb87'),
        'timestamp': 1628166822,
        'totalDifficulty': 28494409340649014490153,
        'transactions': [
            ...
        ],
        'transactionsRoot': HexBytes('0xdfcb68d3a3c41096f4a77569db7956e0a0e750fad185948e54789ea0e51779cb'),
        'uncles': []
    })

    >>> web3.eth.block_number
    12965000

    >>> len(chain)
    12965001  # always +1 to the current block number, because the first block is zero

    >>> chain[0] == web3.eth.get_block(0)
    True

    # for negative index values, the block returned is relative to the most recently mined block
    >>> chain[-1] == web3.eth.get_block('latest')
    True

Accessing Transaction Data
==========================

.. _core-chain-history:

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

    >>> web3.eth.block_number
    0
    >>> chain.mine(50)
    50
    >>> web3.eth.block_number
    50

Time Travel
-----------

You can call :func:`chain.time <Chain.time>` to view the current epoch time:

.. code-block:: python

    >>> chain.time()
    1500000000

To fast forward the clock, call :func:`chain.sleep <Chain.sleep>`.

.. code-block:: python

    >>> chain.sleep(31337)

    >>> chain.time()
    1500031337

Note that sleeping does not mine a new block. Contract view functions that rely on ``block.timestamp`` will be unaffected until you perform a transaction or call :func:`chain.mine <Chain.mine>`.

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

    >>> web3.eth.block_number
    6
    >>> chain.reset()
    >>> web3.eth.block_number
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

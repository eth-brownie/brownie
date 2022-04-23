.. _core-gas:

==============================
Setting Transaction Gas Prices
==============================

Dynamic Fee Transactions
========================

If the network you are interacting with implements EIP-1559, you can use a better fee model when sending transactions. Instead of specifying ``gas_price``, you specify ``priority_fee`` and an optional ``max_fee``.

* ``priority_fee`` determines ``maxPriorityFeePerGas``, which is tipped to the miner. The recommended priority fee can be read from ``chain.priority_fee``.

* ``max_fee`` determines ``maxFeePerGas``, which includes the base fee, which is the same for all transactions in the block and is burned, and your priority fee. The current base fee can be read from ``chain.base_fee``.

Brownie uses ``base_fee * 2 + priority_fee`` as ``max_fee`` if you only specify the priority fee.

    .. code-block:: python

        >>> accounts[0].transfer(accounts[1], priority_fee="2 gwei")
        Transaction sent: 0x090755e0b75648d12b1ada31fa5957a07aadcbe8a34b8f9af59098f1890d1063
          Max fee: 4.0 gwei   Priority fee: 2.0 gwei   Gas limit: 30000000   Nonce: 0
          Transaction confirmed   Block: 1   Gas used: 21000 (0.07%)   Gas price: 2.875 gwei

Dynamic fee transactions do not support (and arguably don't need) gas strategies. The section below only applies to legacy transactions which use ``gas_price``.

Setting Default Dynamic Fees
----------------------------

You can use :func:`network.priority_fee <main.max_fee>` to set a default priority fee for all transactions:

    .. code-block:: python

        >>> from brownie.network import priority_fee
        >>> priority_fee("2 gwei")

Setting the default to ``"auto"`` will dynamically determine the priority fee using :attr:`web3.eth.max_priority_fee <web3.eth.Eth.max_priority_fee>`. Seting to ``None`` will return to legacy-style transactions.

Gas Strategies
==============

Gas strategies are objects that dynamically generate a gas price for a transaction. They can also be used to automatically replace pending transactions within the mempool.

Gas strategies come in three basic types:

* **Simple** strategies provide a gas price once, but do not replace pending transactions.
* **Block** strategies provide an initial price, and optionally replace pending transactions based on the number of blocks that have been mined since the first transaction was broadcast.
* **Time** strategies provide an initial price, and optionally replace pending transactions based on the amount of time that has passed since the first transaction was broadcast.

Using a Gas Strategy
--------------------

To use a gas strategy, first import it from ``brownie.network.gas.strategies``:

    .. code-block:: python

        >>> from brownie.network.gas.strategies import GasNowStrategy
        >>> gas_strategy = GasNowStrategy("fast")

You can then provide the object in the ``gas_price`` field when making a transaction:

    .. code-block:: python

        >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

When the strategy replaces a pending transaction, the returned :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object will be for the transaction that confirms.

During :ref:`non-blocking transactions <core-accounts-non-blocking>`, all pending transactions are available within the :func:`history <brownie.network.state.TxHistory>` object. As soon as one transaction confirms, the remaining dropped transactions are removed.

Setting a Default Gas Strategy
------------------------------

You can use :func:`network.gas_price <main.gas_price>` to set a gas strategy as the default for all transactions:

    .. code-block:: python

        >>> from brownie.network import gas_price
        >>> gas_price(gas_strategy)

Available Gas Strategies
------------------------

.. py:class:: brownie.network.gas.strategies.LinearScalingStrategy(initial_gas_price, max_gas_price, increment=1.125, time_duration=30)

    Time based scaling strategy for linear gas price increase.

    * ``initial_gas_price``: The initial gas price to use in the first transaction
    * ``max_gas_price``: The maximum gas price to use
    * ``increment``: Multiplier applied to the previous gas price in order to determine the new gas price
    * ``time_duration``: Number of seconds between transactions

        .. code-block:: python

            >>> from brownie.network.gas.strategies import LinearScalingStrategy
            >>> gas_strategy = LinearScalingStrategy("10 gwei", "50 gwei", 1.1)

            >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.ExponentialScalingStrategy(initial_gas_price, max_gas_price, time_duration=30)

    Time based scaling strategy for exponential gas price increase.

    The gas price for each subsequent transaction is calculated as the previous price multiplied by `1.1 ** n` where n is the number of transactions that have been broadcast. In this way the price increase starts gradually and ramps up until confirmation.

    * ``initial_gas_price``: The initial gas price to use in the first transaction
    * ``max_gas_price``: The maximum gas price to use
    * ``time_duration``: Number of seconds between transactions

        .. code-block:: python

            >>> from brownie.network.gas.strategies import ExponentialScalingStrategy
            >>> gas_strategy = ExponentialScalingStrategy("10 gwei", "50 gwei")

            >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GasNowStrategy(speed="fast")

    Simple gas strategy for determing a price using the `GasNow <https://www.gasnow.org/>`_ API.

    * ``speed``: The gas price to use based on the API call. Options are rapid, fast, standard and slow.

        .. code-block:: python

            >>> from brownie.network.gas.strategies import GasNowStrategy
            >>> gas_strategy = GasNowStrategy("fast")

            >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GasNowScalingStrategy(initial_speed="standard", max_speed="rapid", increment=1.125, block_duration=2)

    Block based scaling gas strategy using the GasNow API.

    * ``initial_speed``: The initial gas price to use when broadcasting the first transaction. Options are rapid, fast, standard and slow.
    * ``max_speed``: The maximum gas price to use when replacing the transaction. Options are rapid, fast, standard and slow.
    * ``increment``: A multiplier applied to the most recently used gas price in order to determine the new gas price. If the incremented value is less than or equal to the current ``max_speed`` rate, a new transaction is broadcasted. If the current rate for ``initial_speed`` is greater than the incremented rate, it is used instead.
    * ``block_duration``: The number of blocks to wait between broadcasting new transactions.

        .. code-block:: python

            >>> from brownie.network.gas.strategies import GasNowScalingStrategy
            >>> gas_strategy = GasNowScalingStrategy("fast", increment=1.2)

            >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

.. py:class:: brownie.network.gas.strategies.GethMempoolStrategy(position=500, graphql_endpoint=None, block_duration=2)

    Block based scaling gas strategy using Geth's `GraphQL interface <https://eips.ethereum.org/EIPS/eip-1767>`_.

    In order to use this strategy you must be connecting via a Geth node with GraphQL enabled.

    The yielded gas price is determined by sorting transactions in the mempool according to gas price, and returning the price of the transaction at `position`. This is the same technique used by the GasNow API.

    * A position of 200 or less usually places a transaction within the mining block.
    * A position of 500 usually places a transaction within the 2nd pending block.

        .. code-block:: python

            >>> from brownie.network.gas.strategies import GethMempoolStrategy
            >>> gas_strategy = GethMempoolStrategy(200)

            >>> accounts[0].transfer(accounts[1], "1 ether", gas_price=gas_strategy)

Building your own Gas Strategy
------------------------------

To implement your own gas strategy you must subclass from one of the :ref:`gas strategy abstract base classes <api-network-gas-abc>`.

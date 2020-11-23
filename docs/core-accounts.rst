.. _core-accounts:

=====================
Working with Accounts
=====================

The :func:`Accounts <brownie.network.account.Accounts>` container (available as ``accounts`` or just ``a``) allows you to access all your local accounts.

.. code-block:: python

    >>> accounts
    ['0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301', '0xf414d65808f5f59aE156E51B97f98094888e7d92', '0x055f1c2c9334a4e57ACF2C4d7ff95d03CA7d6741', '0x1B63B4495934bC1D6Cb827f7a9835d316cdBB332', '0x303E8684b9992CdFA6e9C423e92989056b6FC04b', '0x5eC14fDc4b52dE45837B7EC8016944f75fF42209', '0x22162F0D8Fd490Bde6Ffc9425472941a1a59348a', '0x1DA0dcC27950F6070c07F71d1dE881c3C67CEAab', '0xa4c7f832254eE658E650855f1b529b2d01C92359','0x275CAe3b8761CEdc5b265F3241d07d2fEc51C0d8']
    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>

Each individual account is represented by an :func:`Account <brownie.network.account.Account>` object that can perform actions such as querying a balance or sending ETH.

.. code-block:: python

    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>
    >>> dir(accounts[0])
    [address, balance, deploy, estimate_gas, nonce, transfer]

The :func:`Account.balance <Account.balance>` method is used to check the balance of an account. The value returned is denominated in :func:`wei <brownie.convert.datatypes.Wei>`.

.. code-block:: python

    >>> accounts[1].balance()
    100000000000000000000

The :func:`Account.transfer <Account.transfer>` method is used to send ether between accounts and perform other simple transactions. As shown in the example below, the amount to transfer may be specified as a string that is converted by :func:`Wei <brownie.convert.datatypes.Wei>`.

.. code-block:: python

    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369'>
    >>> accounts[1].balance()
    110000000000000000000

Generating, Adding, and Unlocking Accounts
==========================================

Newly added accounts are automatically appended to the :func:`Accounts <brownie.network.account.Accounts>` container.

The :func:`Accounts.add <Accounts.add>` method is used to randomly generate a new account:

.. code-block:: python

    >>> accounts.add()
    mnemonic: 'rice cement vehicle ladder end engine tiger gospel toy inspire steel teach'
    <LocalAccount '0x7f1eCD32aF08635A3fB3128108F6Eb0956Efd532'>

You can optionally specify a private key to access a specific account:

.. code-block:: python

    >>> accounts.add('0xca751356c37a98109fd969d8e79b42d768587efc6ba35e878bc8c093ed95d8a9')
    <LocalAccount '0xf6c0182eFD54830A87e4020E13B8E4C82e2f60f0'>

In a development environment, it is possible to send transactions from an address without having that addresses private key. To create an :func:`Account <brownie.network.account.Account>` object from an arbitrary address, use the :func:`Accounts.at <Accounts.at>` method and include ``force=True`` as a keyword argument:

.. code-block:: python

    >>> accounts.at('0x79B2f0CbED2a565C925A8b35f2B402710564F8a2', force=True)
    <Account '0x79B2f0CbED2a565C925A8b35f2B402710564F8a2'>

See :ref:`local-accounts` for more information on working with accounts.

.. _core-accounts-non-blocking:

Broadcasting Multiple Transactions
==================================

Broadcasting a transaction is normally a *blocking action* - Brownie waits until the transaction has confirmed before continuing.
One way to broadcast transactions without blocking is to set ``required_confs = 0``.
This immediately returns a pending :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` and continues without waiting for a confirmation.
Additionally, setting ``silent = True`` suppresses the console output.


.. code-block:: python

    >>> transactions = [
            accounts[0].transfer(accounts[i], "1 ether", required_confs=0, silent=True)
            for i in range(1, 4)
        ]
    >>> [tx.status for tx in transactions]
    [1, -1, -1]

These transactions are initially pending (``status == -1``) and appear yellow in the console.

Replacing Transactions
======================

The :func:`TransactionReceipt.replace <TransactionReceipt.replace>` method can be used to replace underpriced transactions while they are still pending:

.. code-block:: python

    >>> tx = accounts[0].transfer(accounts[1], 100, required_confs=0, gas_price="1 gwei")
    Transaction sent: 0xc1aab54599d7875fc1fe8d3e375abb0f490cbb80d5b7f48cedaa95fa726f29be
        Gas price: 13.0 gwei   Gas limit: 21000   Nonce: 3
    <Transaction object '0xc1aab54599d7875fc1fe8d3e375abb0f490cbb80d5b7f48cedaa95fa726f29be'>

    >>> tx.replace(1.1)
    Transaction sent: 0x9a525e42b326c3cd57e889ad8c5b29c88108227a35f9763af33dccd522375212
        Gas price: 14.3 gwei   Gas limit: 21000   Nonce: 3
    <Transaction '0x9a525e42b326c3cd57e889ad8c5b29c88108227a35f9763af33dccd522375212'>

All pending transactions are available within the :func:`history <brownie.network.state.TxHistory>` object. As soon as one transaction confirms, the remaining dropped transactions are removed. See the documentation on :ref:`accessing transaction history <core-chain-history>` for more info.

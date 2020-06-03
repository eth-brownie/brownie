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

=========================
Running Many Transactions
=========================

Running any transaction will by default wait until that transaction is completed before continuing. There are two ways to run many transactions at the same time without waiting:

1. Set the required confirmations of the transaction to ``0``.

This will immediately return a pending :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` and continue without waiting for a confirmation. Additionally, setting ``silent=True`` will suppress the console output.

.. code-block:: python

    >>> transactions = [
            accounts[0].transfer(accounts[i], "1 ether", required_confs=0, silent=True)
            for i in range(1, 4)
        ]
    >>> [tx.status for tx in transactions]
    [1, -1, -1]

These transactions will initially be pending (``status = -1``) and confirm in a seperate thread in the background.

2. Run the transactions in individual threads.

A more advanced usage is to create a thread for each transaction. Brownie will automatically set the correct nonces and ensure thread safety.

.. code-block:: python

    import threading

    def send_confirmed_ether(recipient):
        accounts[0].transfer(recipient, "1 ether", required_confs=4, silent=True)
        print(f"Confirmed tx to send ether to {recipient}.")

    threads = [
        threading.Thread(target=send_confirmed_ether, args=(accounts[i],), daemon=True)
        for i in range(1, 4)
    ]

    for t in threads:
        t.start()
    print("Transactions queued.")

    # ... code while you wait for confirmations ...

    for t in threads:
        t.join()
    print("All transactions confirmed.")

    # Output
    Transactions queued.
    Confirmed tx to send ether to 0x33A4622B82D4c04a53e170c638B944ce27cffce3.
    Confirmed tx to send ether to 0x0063046686E46Dc6F15918b61AE2B121458534a5.
    Confirmed tx to send ether to 0x21b42413bA931038f35e7A5224FaDb065d297Ba3.
    Transactions confirmed.

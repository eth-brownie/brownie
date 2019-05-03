.. _interaction:

==========================
Interacting with a Project
==========================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop.  It's also a great starting point to familiarize yourself with Brownie's functionality.

The console feels very similar to a regular python interpreter. From inside a project folder, load it by typing:

::

    $ brownie console

Brownie will compile the contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.

.. hint::

    You can call the builtin ``dir`` method to see available methods and attributes for any class. Classes, methods and attributes are highlighted in different colors.

    You can also call ``help`` on most classes and methods to get detailed information on how they work.

Working with Accounts
=====================

The ``accounts`` container (or just ``a``) allows you to access all your local accounts.

.. code-block:: python

    >>> accounts
    ['0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301', '0xf414d65808f5f59aE156E51B97f98094888e7d92', '0x055f1c2c9334a4e57ACF2C4d7ff95d03CA7d6741', '0x1B63B4495934bC1D6Cb827f7a9835d316cdBB332', '0x303E8684b9992CdFA6e9C423e92989056b6FC04b', '0x5eC14fDc4b52dE45837B7EC8016944f75fF42209', '0x22162F0D8Fd490Bde6Ffc9425472941a1a59348a', '0x1DA0dcC27950F6070c07F71d1dE881c3C67CEAab', '0xa4c7f832254eE658E650855f1b529b2d01C92359','0x275CAe3b8761CEdc5b265F3241d07d2fEc51C0d8']
    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>

Each individual account is represented by a class that can perform actions such as querying balance or sending ETH.

.. code-block:: python

    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>
    >>> dir(accounts[0])
    [address, balance, deploy, estimate_gas, nonce, transfer]
    >>> accounts[1].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369'>
    >>> accounts[1].balance()
    110000000000000000000

You can import accounts with ``accounts.add``, which takes a private key as the only argument. If you do not enter a private key one is randomly generated.

.. code-block:: python

    >>> len(accounts)
    10
    >>> accounts.add("ce7594141801cf9b81b7ccb09e30395fc9e9e5940b1c01eed6434588bd726f94")
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>
    >>> len(accounts)
    11
    >>> accounts[10]
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>
    >>> accounts.add()
    <Account object '0xc1b3a737C147E8d85f600F8082f42F0511ED5278'>
    >>> len(accounts)
    12

Imported accounts may be saved with an identifier and then loaded again at a later date. Account data is saved in a standard json `keystore <https://goethereumbook.org/keystore/>`__ file that is compatible with most wallets.

.. code-block:: python

    >>> accounts.add()
    <LocalAccount object '0xa9c2DD830DfFE8934fEb0A93BAbcb6e823e1FF05'>
    >>> accounts[-1].save('my_account')
    Enter the password to encrypt this account with:
    Saved to brownie/data/accounts/my_account.json
    >>> accounts.load('my_account')
    Enter the password for this account:
    <LocalAccount object '0xa9c2DD830DfFE8934fEb0A93BAbcb6e823e1FF05'>

Working with Contracts
======================

Each contract in the project has a ``ContractDeployer`` class, which allows you to deploy new contracts and is a container that holds specific instances of that contract. To deploy a contract, include the deploying account as the first argument followed by the constructor arguments.

.. code-block:: python

    >>> type(Token)
    <class 'brownie.network.contract.ContractContainer'>
    >>> Token
    []
    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>
    >>> t = Token.deploy(accounts[1], "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>>
    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token
    [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]
    >>> Token[0]
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

Alternatively, you can deploy from ``account`` with the contract as the first argument.

.. code-block:: python

    >>> Token
    []
    >>> t = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>>
    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token
    [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]
    >>> Token[0]
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

You can also use ``ContractDeployer.at`` to access an already existing contract.

.. code-block:: python

    >>> Token.at("0x5419710735c2D6c3e4db8F30EF2d361F70a4b380")
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

External and public contract methods are callable by class methods of the same name. Arguments given to these objects are converted using the methods outlined in the :ref:`_type-conversions` section of the API documentation.

.. code-block:: python

    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address _owner)'>
    >>> Token[0].transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>

If the contract method has a state mutability of ``view`` or ``pure``, the related class method is of type :ref:`api-contract-call`. Calling this object will result in a call to the method. If you wish to call the method as a transaction you can use ``ContractCall.transact``.

.. code-block:: python

    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000
    >>> tx = Token[0].balanceOf.transact(accounts[0])

    Transaction sent: 0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8
    Token.balanceOf confirmed - block: 3   gas used: 23222 (18.85%)
    <Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>
    >>> tx.return_value
    1000000000000000000000

For state changing methods the type is :ref:`api-contract-tx`. Calls to this object will perform a transaction. If you wish to call the contract method without a transaction, use ``ContractTx.call``.

For transactions you can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].transfer(accounts[1], "1 ether", {'from': accounts[0]})

    Transaction sent: 0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e
    Token.transfer confirmed - block: 4   gas used: 51019 (33.78%)
    <Transaction object '0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e'>
    >>> Token[0].transfer.call(accounts[1], "1 ether", {'from': accounts[0]})
    True

Transactions
============

Each transaction returns a :ref:`api-network-tx` object. This object contains all relevant information about the transaction, as well as various methods to aid in debugging if it reverted.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], "1 ether", {'from': accounts[0]})

    Transaction sent: 0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b
    Token.transfer confirmed - block: 2   gas used: 51019 (33.78%)
    <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>
    >>> tx
    <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>


To get human-readable information on a transaction, use ``TransactionReceipt.info()``.

.. code-block:: python

    >>> tx.info()

    Transaction was Mined
    ---------------------
    Tx Hash: 0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b
    From: 0x4FE357AdBdB4C6C37164C54640851D6bff9296C8
    To: 0xDd18d6475A7C71Ee33CEBE730a905DbBd89945a1
    Value: 0
    Function: Token.transfer
    Block: 2
    Gas Used: 51019 / 151019 (33.8%)

    Events In This Transaction
    --------------------------
    Transfer
        from: 0x4fe357adbdb4c6c37164c54640851d6bff9296c8
        to: 0xfae9bc8a468ee0d8c84ec00c8345377710e0f0bb
        value: 1000000000000000000

Events are stored at ``TransactionReceipt.events`` using the :ref:`api-types-eventdict` class.

.. code-block:: python

    >>> history[-2].events
    {
        'Transfer': {
            'from': "0x4fe357adbdb4c6c37164c54640851d6bff9296c8",
            'to': "0xfae9bc8a468ee0d8c84ec00c8345377710e0f0bb",
            'value': 1000000000000000000
        }
    }

When a transaction reverts you will still receive a ``TransactionReceipt`` but it will show as reverted. If an error string is given, it will be displayed in brackets and highlighted in red.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], "1 ether", {'from': accounts[3]})

    Transaction sent: 0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a
    Token.transfer confirmed (Insufficient Balance) - block: 2   gas used: 23858 (19.26%)
    <Transaction object '0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a'>

You can use ``TransactionReceipt.error()`` to see the section of the source code that caused the revert.

.. code-block:: python

    >>> tx.error()
    File "contracts/Token.sol", line 62, in function transfer
        }

        function transfer(address _to, uint256 _value) public returns (bool) {
            require(balances[msg.sender] >= _value, "Insufficient Balance");
            balances[msg.sender] = balances[msg.sender].sub(_value);
            balances[_to] = balances[_to].add(_value);
            emit Transfer(msg.sender, _to, _value);

You can also call ``TransactionReceipt.call_trace()`` to see all the contract jumps, internal and external, that occured prior to the revert.

.. code-block:: python

    >>> tx = Token[0].transferFrom(accounts[2], accounts[3], "10000 ether")

    Transaction sent: 0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753
    Token.transferFrom confirmed (reverted) - block: 4   gas used: 25425 (26.42%)

    >>> tx.call_trace()
    Token.transferFrom 0 (0x4C2588c6BFD533E0a27bF7572538ca509f31882F)
        Token.sub 86 (0x4C2588c6BFD533E0a27bF7572538ca509f31882F)

Unconfirmed Transactions
------------------------

If you are working on a chain where blocks are not mined automatically, you can press ``CTRL-C`` while waiting for a transaction to confirm and return to the console.  You will still be returned a ``TransactionReceipt``, however it will be marked as pending (printed in yellow). A notification is displayed when the transaction confirms.

If you send another transaction from the same account before the previous one has confirmed, it will still broadcast with the next sequential nonce.

You can view the ``history`` list to quickly view the status of any pending transactions without having to assign them unique names.

.. _interaction:

===================================
Project Interaction via the Console
===================================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. It's also a great starting point to familiarize yourself with Brownie's functionality.

The console feels very similar to a regular python interpreter. From inside a project folder, load it by typing:

::

    $ brownie console

Brownie will compile the contracts, launch or attach to :ref:`test-rpc`, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.

.. hint::

    You can call the builtin ``dir`` method to see available methods and attributes for any class. Classes, methods and attributes are highlighted in different colors.

    You can also call ``help`` on most classes and methods to get detailed information on how they work.

Accounts
========

The :ref:`api-network-accounts` container (available as ``accounts`` or just ``a``) allows you to access all your local accounts.

.. code-block:: python

    >>> accounts
    ['0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301', '0xf414d65808f5f59aE156E51B97f98094888e7d92', '0x055f1c2c9334a4e57ACF2C4d7ff95d03CA7d6741', '0x1B63B4495934bC1D6Cb827f7a9835d316cdBB332', '0x303E8684b9992CdFA6e9C423e92989056b6FC04b', '0x5eC14fDc4b52dE45837B7EC8016944f75fF42209', '0x22162F0D8Fd490Bde6Ffc9425472941a1a59348a', '0x1DA0dcC27950F6070c07F71d1dE881c3C67CEAab', '0xa4c7f832254eE658E650855f1b529b2d01C92359','0x275CAe3b8761CEdc5b265F3241d07d2fEc51C0d8']
    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>

Each individual account is represented by an :ref:`api-network-account` object that can perform actions such as querying a balance or sending ETH.

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

Contracts
=========

Deploying
---------

Each deployable contract and library has a :ref:`api-network-contractcontainer` class, used to deploy new contracts and access already existing ones.

To deploy a contract, call the ``ContractContainer.deploy`` method with the constructor arguments, with a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. The dictionary must include a ``from`` value that specifies the ``Account`` to deploy the contract from.

A :ref:`Contract <api-network-contract>` object is returned and also appended to the ``ContractContainer``.

.. code-block:: python

    >>> type(Token)
    <class 'brownie.network.contract.ContractContainer'>
    >>> Token
    []
    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>
    >>> t = Token.deploy("Test Token", "TST", 18, "1000 ether", {'from': accounts[1]})

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

Alternatively, you can deploy from ``Account`` with the ``ContractContainer`` as the first argument.

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

You can also use ``ContractContainer.at`` to create a new ``Contract`` object for an already deployed contract.

.. code-block:: python

    >>> Token.at("0x5419710735c2D6c3e4db8F30EF2d361F70a4b380")
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

Unlinked Libraries
------------------

If a contract requires a library, Brownie will automatically link to the most recently deployed one. If the required library has not been deployed yet an ``UndeployedLibrary`` exception is raised.

.. code-block:: python

    >>> accounts[0].deploy(MetaCoin)
      File "brownie/network/contract.py", line 167, in __call__
        f"Contract requires '{library}' library but it has not been deployed yet"
    UndeployedLibrary: Contract requires 'ConvertLib' library but it has not been deployed yet

    >>> accounts[0].deploy(ConvertLib)
    Transaction sent: 0xff3f5cff35c68a73658ad367850b6fa34783b4d59026520bd61b72b6613d871c
    ConvertLib.constructor confirmed - block: 1   gas used: 95101 (48.74%)
    ConvertLib deployed at: 0x08c4C7F19200d5636A1665f6048105b0686DFf01
    <ConvertLib Contract object '0x08c4C7F19200d5636A1665f6048105b0686DFf01'>

    >>> accounts[0].deploy(MetaCoin)
    Transaction sent: 0xd0969b36819337fc3bac27194c1ff0294dd65da8f57c729b5efd7d256b9ecfb3
    MetaCoin.constructor confirmed - block: 2   gas used: 231857 (69.87%)
    MetaCoin deployed at: 0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f
    <MetaCoin Contract object '0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f'>

Accessing Contract Methods
--------------------------

External and public contract methods are callable from the ``Contract`` object via class methods of the same name. Arguments given to these objects are converted using the methods outlined in the :ref:`type-conversions` section of the API documentation.

.. code-block:: python

    >>> Token[0].transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>
    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address _owner)'>

Transactions
************

For state changing contract methods, the related class method is :ref:`api-contract-tx`. Calls to this object perform a transaction and return a :ref:`api-network-tx` object. If you wish to call the contract method without a transaction, use the ``ContractTx.call`` method.

For transactions you can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``from`` value, the transaction will be sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].transfer(accounts[1], "1 ether", {'from': accounts[0]})

    Transaction sent: 0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e
    Token.transfer confirmed - block: 4   gas used: 51019 (33.78%)
    <Transaction object '0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e'>
    >>> Token[0].transfer.call(accounts[1], "1 ether", {'from': accounts[0]})
    True

Calls
*****

If the contract method has a state mutability of ``view`` or ``pure``, the related class method type is :ref:`api-contract-call`. Calling this object will call the contract method and return the result. If you wish to access the method via a transaction you can use ``ContractCall.transact``.

.. code-block:: python

    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000
    >>> tx = Token[0].balanceOf.transact(accounts[0])

    Transaction sent: 0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8
    Token.balanceOf confirmed - block: 3   gas used: 23222 (18.85%)
    <Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>
    >>> tx.return_value
    1000000000000000000000

Ether Values
============

Brownie uses the :ref:`Wei<wei>` class when a value is meant to represent an amount of ether. ``Wei`` is a subclass of ``int`` that converts strings, scientific notation and hex strings into wei denominated integers:

.. code-block:: python

    >>> Wei("1 ether")
    1000000000000000000
    >>> Wei("12.49 gwei")
    12490000000
    >>> Wei("0.029 shannon")
    29000000
    >>> Wei(8.38e32)
    838000000000000000000000000000000

It also converts other values to ``Wei`` before performing comparisons, addition or subtraction:

    >>> Wei(1e18) == "1 ether"
    True
    >>> Wei("1 ether") < "2 ether"
    True
    >>> Wei("1 ether") - "0.75 ether"
    250000000000000000

Whenever a Brownie method takes an input referring to an amount of ether, the given value is converted to ``Wei``. Balances and ``uint``/``int`` values returned in contract calls and events are given in ``Wei``.

.. code-block:: python

    >>> accounts[0].balance()
    100000000000000000000
    >>> type(accounts[0].balance())
    <class 'brownie.convert.Wei'>

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

.. _event-data:

Accessing Event Data
--------------------

Events are stored at ``TransactionReceipt.events`` using the :ref:`api-network-eventdict` class. ``EventDict`` hybrid container with both dict-like and list-like properties.

.. note::

    Event data is still available when a transaction reverts.

.. code-block:: python

    >>> tx.events
    {
        'CountryModified': [
            {
                'country': 1,
                'limits': (0,0,0,0,0,0,0,0),
                'minrating': 1,
                'permitted': True
            },
            {
                'country': 2,
                'limits': (0,0,0,0,0,0,0,0),
                'minrating': 1,
                'permitted': True
            }
        ],
        'MultiSigCallApproved': [
            {
                'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
                'callSignature': "0xa513efa4",
                'caller': "0xF9c1fd2f0452FA1c60B15f29cA3250DfcB1081b9",
                'id': "0x8be1198d7f1848ebeddb3f807146ce7d26e63d3b6715f27697428ddb52db9b63"
            }
        ]
    }

Use it as a dict for looking at specific events when the sequence they are fired in does not matter:

.. code-block:: python

    >>> len(tx.events)
    3
    >>> len(tx.events['CountryModified'])
    2
    >>> 'MultiSigCallApproved' in tx.events
    True
    >>> tx.events['MultiSigCallApproved']
    {
        'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
        'callSignature': "0xa513efa4",
        'caller': "0xF9c1fd2f0452FA1c60B15f29cA3250DfcB1081b9",
        'id': "0x8be1198d7f1848ebeddb3f807146ce7d26e63d3b6715f27697428ddb52db9b63"
    }

Or as a list when the sequence is important, or more than one event of the same type was fired:

.. code-block:: python

    >>> tx.events[1].name
    'CountryModified'
    >>> tx.events[1]
    {
        'country': 1,
        'limits': (0,0,0,0,0,0,0,0),
        'minrating': 1,
        'permitted': True
    }

Reverted Transactions
---------------------

When a transaction reverts in the console you are still returned a ``TransactionReceipt``, but it will show as reverted. If an error string is given, it will be displayed in brackets and highlighted in red.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], "1 ether", {'from': accounts[3]})

    Transaction sent: 0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a
    Token.transfer confirmed (Insufficient Balance) - block: 2   gas used: 23858 (19.26%)
    <Transaction object '0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a'>

You can use ``TransactionReceipt.error()`` to see the section of the source code that caused the revert:

.. code-block:: python

    >>> tx.error()
    File "contracts/Token.sol", line 62, in function transfer
        }

        function transfer(address _to, uint256 _value) public returns (bool) {
            require(balances[msg.sender] >= _value, "Insufficient Balance");
            balances[msg.sender] = balances[msg.sender].sub(_value);
            balances[_to] = balances[_to].add(_value);
            emit Transfer(msg.sender, _to, _value);

Or ``TransactionReceipt.traceback()`` for a full traceback leading up to the revert:

.. code-block:: python

    >>> tx.traceback()
    Traceback for '0x9542e92a904e9d345def311ea52f22c3191816c6feaf7286f9b48081ab255ffa':
    Trace step 99, program counter 1699:
      File "contracts/Token.sol", line 67, in Token.transfer:
        balances[msg.sender] = balances[msg.sender].sub(_value);
    Trace step 110, program counter 1909:
      File "contracts/SafeMath.sol", line 9, in SafeMath.sub:
        require(b <= a);

You can also call ``TransactionReceipt.call_trace()`` to see all the contract jumps, internal and external, that occured during the transaction. This method is available for all transactions, not only those that reverted.

.. code-block:: python

    >>> tx = Token[0].transferFrom(accounts[2], accounts[3], "10000 ether")

    Transaction sent: 0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753
    Token.transferFrom confirmed (reverted) - block: 4   gas used: 25425 (26.42%)

    >>> tx.call_trace()
    Call trace for '0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753':
    Token.transfer 0:244  (0x4A32104371b05837F2A36dF6D850FA33A92a178D)
      ∟ Token.transfer 72:226
      ∟ SafeMath.sub 100:114
      ∟ SafeMath.add 149:165

See :ref:`debug` for more information on debugging reverted transactions.

Unconfirmed Transactions
------------------------

If you are working on a chain where blocks are not mined automatically, you can press ``CTRL-C`` while waiting for a transaction to confirm and return to the console.  You will still be returned a ``TransactionReceipt``, however it will be marked as pending (printed in yellow). A notification is displayed when the transaction confirms.

If you send another transaction from the same account before the previous one has confirmed, it will still broadcast with the next sequential nonce.

Accessing Historic Transactions
-------------------------------

The :ref:`api-network-history` object, available as ``history``, holds all the transactions that have been broadcasted. You can use it to access ``TransactionReceipt`` objects if you did not assign them a unique name when making the call.

.. code-block:: python

    >>> history
    [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>, <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>]

The Local Test Environment
==========================

Brownie is designed to use `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__ as a local development environment.  Functionality such as snapshotting and time travel is accessible via the :ref:`rpc` object, available as ``rpc``:

.. code-block:: python

    >>> rpc
    <brownie.network.rpc.Rpc object at 0x7f720f65fd68>

``Rpc`` is useful when you need to perform tests dependent on time:

.. code-block:: python

    >>> rpc.time()
    1557151189
    >>> rpc.sleep(100)
    >>> rpc.time()
    1557151289

Or for returning to a previous state during tests:

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

See :ref:`test-rpc` for more information on how to use ``Rpc``.

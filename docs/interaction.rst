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

You can call any available contract method or send a transaction by using the class method of the same name, with the intended arguments.

For transactions you can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address)'>
    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000
    >>> Token[0].transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>
    >>> Token[0].transfer(accounts[1], "10 ether", {'from':accounts[0]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 3   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>
    >>> Token[0].balanceOf(accounts[1])
    10000000000000000000

If the gas limit is set to calculate automatically, transactions that revert will raise a ``VirtualMachineError``. If the gas limit is fixed they will return a ``TransactionReceipt`` marked as reverted (printed in red).

Unconfirmed Transactions
========================

If you are working on a chain where blocks are not mined automatically, you can press ``CTRL-C`` while waiting for a transaction to confirm and return to the console.  You will still be returned a ``TransactionReceipt instance``, however it will be marked as pending (printed in yellow). A notification is displayed when the transaction confirms.

If you send another transaction from the same account before the previous one has confirmed, it will still broadcast with the next sequential nonce.

You can view the ``history`` list to quickly view the status of any pending transactions without having to assign them unique names.

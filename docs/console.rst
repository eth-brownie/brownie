=================
Using The Console
=================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop.

The console feels similar to a normal python interpreter. Load it by typing:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`. Below are some examples of common tasks.

Configuration
=============

You can view and edit the configuration settings through the ``config`` dictionary. Changes that are made are only active as long as brownie is running - modifying the dictionary does not modify ``config.json``. See :ref:`config` for more information.

Basic Functionality
===================

The following methods, classes and containers are available:

* ``gas(value)``: View or modify the current gas limit.
* ``history``: A list containing every transaction broadcasted during the console session.
* ``logging(tx=None, exc=None)``: Adjusts the console verbosity.
* ``rpc``: Methods for interacting with the local RPC.
* ``reset(network=None)``: Reset the local RPC environment.
* ``run(script)``: Executes the ``main`` function of a script in the ``scripts/`` folder.
* ``wei(value)``: Converts strings and floats to an integer denoted in wei
* ``web3``: A minimal implementation of the `Web3 API <https://web3py.readthedocs.io/en/stable/web3.main.html>`__

You can use the builtin ``dir`` function to see available methods and attributes for any class. Classes, methods and attributes are highlighted in different colors.

Working with Accounts
=====================

The container class ``accounts`` (or just ``a``) allows you to access all your local accounts.

.. code-block:: python

    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>
    >>> accounts[1].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369'>
    >>> accounts[1].balance()
    110000000000000000000

You can generate accounts from a seed phrase using ``accounts.mnemonic``. The generation scheme is compatible with MetaMask and other popular wallets.

.. code-block:: python

    >>> accounts.clear()
    >>> len(accounts)
    0
    >>> accounts.mnemonic("caught rare sport prison casino post object exile clutch enough race pulp")
    >>> len(accounts)
    10

You can also import accounts individually with ``accounts.add``, which takes a private key as the only argument. If you do not enter a private key one is randomly generated.

.. code-block:: python

    >>> len(accounts)
    20
    >>> accounts.add("ce7594141801cf9b81b7ccb09e30395fc9e9e5940b1c01eed6434588bd726f94")
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>
    >>> len(accounts)
    21
    >>> accounts[20]
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>
    >>> accounts.add()
    <Account object '0xc1b3a737C147E8d85f600F8082f42F0511ED5278'>

Working with Contracts
======================

Each contract in the project has a ``ContractDeployer`` class, which allows you to deploy new contracts and is a container that holds specific instances of that contract. To deploy a contract, include the deploying account as the first argument followed by the constructor arguments.

.. code-block:: python

    >>> Token
    []
    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string,string,uint256,uint256)'>
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
    <ContractTx object 'transfer(address,uint256)'>
    >>> Token[0].transfer(accounts[1], "10 ether", {'from':accounts[0]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 3   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>
    >>> Token[0].balanceOf(accounts[1])
    10000000000000000000

If the gas limit is set to calculate automatically, transactions that revert will raise a ``VirtualMachineError``. If the gas limit is fixed they will return a ``TransactionReceipt`` marked as reverted (printed in red).

Debugging Tools
===============

.. note:: Debugging functionality relies on the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#debug_tracetransaction>`__ RPC method. If you are using Infura this attribute is not available.

When a transaction reverts and the gas limit is not set to automatic, you are still returned a ``TransactionReceipt``. From this instance you can call the following attributes and methods to help determine why it reverted:

* ``TransactionReceipt.revert_msg``: The error string returned when the EVM reverted, if any.
* ``TransactionReceipt.trace``: The call trace structLog as a list.
* ``TransactionReceipt.events``: The events that were emitted before the transaction reverted.
* ``TransactionReceipt.error()``: Displays the filename, line number, and line of code that caused the revert.
* ``TransactionReceipt.call_trace()``: Displays the sequence of contracts and functions called while executing this transaction, and the structLog list index where each call or jump occured. Any functions that terminated with a ``REVERT`` opcode are highlighted in red.

Alerts and Callbacks
====================

You can use the :ref:`api_alert` module to receive notifications or setup callbacks whenever a state change occurs.

.. code-block:: python

    >>> alert.new(accounts[1].balance, msg="Account 1 balance has changed from {} to {}")
    <lib.components.alert.Alert object at 0x7f9fd25d55f8>
    >>> alert.show()
    [<lib.components.alert.Alert object at 0x7f9fd25d55f8>]
    >>> accounts[2].transfer(accounts[1], "1 ether")

    Transaction sent: 0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0x912d6ac704e7aaac01be159a4a36bbea0dc0646edb205af95b6a7d20945a2fd2'>
    ALERT: Account 1 balance has changed from 100000000000000000000 to 101000000000000000000

.. code-block:: python

    >>> alert.new(accounts[3].balance, msg="Account 3 balance has changed from {} to {}")
    <lib.components.alert.Alert object at 0x7fc743e415f8>
    >>> def on_receive(old_value, new_value):
    ...     accounts[2].transfer(accounts[3], new_value-old_value)
    ...
    >>> alert.new(accounts[2].balance, callback=on_receive)
    <lib.components.alert.Alert object at 0x7fc743e55cf8>
    >>> accounts[1].transfer(accounts[2],"1 ether")

    Transaction sent: 0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0xbd1bade3862f181359f32dac02ffd1d145fdfefc99103ca0e3d28ffc7071a9eb'>

    Transaction sent: 0x8fcd15e38eed0a5c9d3d807d593b0ea508ba5abc892428eb2e0bb0b8f7dc3083
    Transaction confirmed - block: 2   gas spent: 21000
    ALERT: Account 3 balance has changed from 100000000000000000000 to 101000000000000000000

Unconfirmed Transactions
========================

If you are working on a chain where blocks are not mined automatically, you can press ``CTRL-C`` while waiting for a transaction to confirm and return to the console.  You will still be returned a ``TransactionReceipt instance``, however it will be marked as pending (printed in yellow). A notification is displayed when the transaction confirms.

If you send another transaction from the same account before the previous one has confirmed, it will still broadcast with the next sequential nonce.

You can view the ``history`` list to quickly view the status of any pending transactions without having to assign them unique names.

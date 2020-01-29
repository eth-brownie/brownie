.. _core-contracts:

======================
Working with Contracts
======================

Deploying Contracts
===================

Each time Brownie is loaded it will automatically compile your project and create :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects for each deployable contract. This object is a container used to access individual deployments. It is also used to deploy new contracts.

.. code-block:: python

    >>> Token
    []
    >>> type(Token)
    <class 'brownie.network.contract.ContractContainer'>
    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>

:func:`ContractContainer.deploy <ContractContainer.deploy>` is used to deploy a new contract.

.. code-block:: python

    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>

It must be called with the contract constructor arguments, and a dictionary of :ref:`transaction parameters <transaction-parameters>` containing  a ``from`` field that specifies which :func:`Account <brownie.network.account.Account>` to deploy the contract from.

.. code-block:: python

    >>> Token.deploy("Test Token", "TST", 18, "1000 ether", {'from': accounts[1]})

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>


Calling :func:`ContractContainer.deploy <ContractContainer.deploy>` returns a :func:`Contract <brownie.network.contract.ProjectContract>` object. The returned object is also appended to the :func:`ContractContainer <brownie.network.contract.ContractContainer>`.

.. code-block:: python

    >>> t = Token.deploy("Test Token", "TST", 18, "1000 ether", {'from': accounts[1]})

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token
    [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]

Unlinked Libraries
------------------

If a contract requires a `library <https://solidity.readthedocs.io/en/v0.6.0/contracts.html#libraries>`_, Brownie will automatically link to the most recently deployed one. If the required library has not been deployed yet an :func:`UndeployedLibrary <brownie.exceptions.UndeployedLibrary>` exception is raised.

.. code-block:: python

    >>> MetaCoin.deploy({'from': accounts[0]})
      File "brownie/network/contract.py", line 167, in __call__
        f"Contract requires '{library}' library but it has not been deployed yet"
    UndeployedLibrary: Contract requires 'ConvertLib' library but it has not been deployed yet

    >>> Convert.deploy({'from': accounts[0]})
    Transaction sent: 0xff3f5cff35c68a73658ad367850b6fa34783b4d59026520bd61b72b6613d871c
    ConvertLib.constructor confirmed - block: 1   gas used: 95101 (48.74%)
    ConvertLib deployed at: 0x08c4C7F19200d5636A1665f6048105b0686DFf01
    <ConvertLib Contract object '0x08c4C7F19200d5636A1665f6048105b0686DFf01'>

    >>> MetaCoin.deploy({'from': accounts[0]})
    Transaction sent: 0xd0969b36819337fc3bac27194c1ff0294dd65da8f57c729b5efd7d256b9ecfb3
    MetaCoin.constructor confirmed - block: 2   gas used: 231857 (69.87%)
    MetaCoin deployed at: 0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f
    <MetaCoin Contract object '0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f'>

Interacting with your Contracts
===============================

Once a contract has been deployed, you can interact with it via via `calls` and `transactions`.

    * **Transactions** are broadcast to the network and recorded on the blockchain. They cost ether to run, and are able to alter the state to the blockchain.
    * **Calls** are used to execute code on the network without broadcasting a transaction. They are free to run, and cannot alter the state of the blockchain in any way. Calls are typically used to retrieve a storage value from a contract using a getter method.

You may call or send a transaction to any public function within a contract. However, depending on the code, there is always a preferred method:

    * In Solidity, callable methods are labelled as `view <https://solidity.readthedocs.io/en/v0.6.0/contracts.html#view-functions>`_ or `pure <https://solidity.readthedocs.io/en/v0.6.0/contracts.html#pure-functions>`_
    * In Vyper, callable methods include the `@constant <https://vyper.readthedocs.io/en/latest/structure-of-a-contract.html#decorators>`_ decorator.

All public contract methods are available from the :func:`Contract <brownie.network.contract.ProjectContract>` object via class methods of the same name.

.. code-block:: python

    >>> Token[0].transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>
    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address _owner)'>

Transactions
------------

State-changing contract methods are called via a :func:`ContractTx <brownie.network.contract.ContractTx>` object. This object performs a transaction and returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`.

You may optionally include a dictionary of :ref:`transaction parameters <transaction-parameters>` as the final argument. If you do not do this, or do not specify a ``from`` value within the parameters, the transaction is sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].transfer(accounts[1], "1 ether", {'from': accounts[0]})

    Transaction sent: 0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e
    Token.transfer confirmed - block: 4   gas used: 51019 (33.78%)
    <Transaction object '0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e'>

If you wish to call the contract method without a transaction, use the :func:`ContractTx.call <ContractTx.call>` method.

.. code-block:: python

    >>> Token[0].transfer.call(accounts[1], "1 ether", {'from': accounts[0]})
    True

.. _transaction-parameters:

Transaction Parameters
**********************

When executing a transaction to a contract, you can optionally include an dictionary of transaction parameters as the final input. It may contain the following values:

    * ``from``: the :func:`Account <brownie.network.account.Account>` that the transaction it sent from. If not given, the transaction is sent from the account that deployed the contract.
    * ``gas_limit``: The amount of gas provided for transaction execution, in wei. If not given, the gas limit is determined using ``web3.eth.estimateGas``.
    * ``gas_price``: The gas price for the transaction, in wei. If not given, the gas price is set according to ``web3.eth.getPrice``.
    * ``amount``: The amount of Ether to include with the transaction, in wei.

All integer values can also be given as strings that will be converted by :func:`Wei <brownie.convert.datatypes.Wei>`.

.. note::

    To maintain compatibility with ``web3.eth.sendTransaction``, you can use ``gas``, ``gasPrice`` and ``value`` as aliases for ``gas_limit``, ``gas_price``, and ``amount``.

Calls
-----

Contract methods that do not alter the state are called via a :func:`ContractCall <brownie.network.contract.ContractCall>` object. This object will call the contract method without broadcasting a transaction, and return the result.

.. code-block:: python

    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000

If you wish to access the method via a transaction you can use :func:`ContractCall.transact <ContractCall.transact>`.

.. code-block:: python

    >>> tx = Token[0].balanceOf.transact(accounts[0])

    Transaction sent: 0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8
    Token.balanceOf confirmed - block: 3   gas used: 23222 (18.85%)
    <Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>
    >>> tx.return_value
    1000000000000000000000

Contracts Outside of your Project
=================================

It is also possible to create a :func:`Contract <brownie.network.contract.Contract>` object using only an `ABI <https://solidity.readthedocs.io/en/latest/abi-spec.html#json>`_. In this way you can interact with already deployed contracts that are not a part of your core project.

To create a :func:`Contract <brownie.network.contract.Contract>` from an ABI:

.. code-block:: python

    >>> from brownie import Contract
    >>> Contract('0x79447c97b6543F6eFBC91613C655977806CB18b0', "Token", abi)
    <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

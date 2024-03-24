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

    >>> Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[1]})

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>


Calling :func:`ContractContainer.deploy <ContractContainer.deploy>` returns a :func:`ProjectContract <brownie.network.contract.ProjectContract>` object. The returned object is also appended to the :func:`ContractContainer <brownie.network.contract.ContractContainer>`.

.. code-block:: python

    >>> t = Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[1]})

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

All public contract methods are available from the :func:`ProjectContract <brownie.network.contract.ProjectContract>` object via class methods of the same name.

.. code-block:: python

    >>> Token[0].transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>
    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address _owner)'>

When a contract source includes `NatSpec documentation <https://solidity.readthedocs.io/en/latest/natspec-format.html>`_, you can view it via the :func:`ContractCall.info <ContractCall.info>` method:

.. code-block:: python

    >>> Token[0].transfer.info()
    transfer(address _to, uint256 _value)
      @dev transfer token for a specified address
      @param _to The address to transfer to.
      @param _value The amount to be transferred.


Transactions
------------

State-changing contract methods are called via a :func:`ContractTx <brownie.network.contract.ContractTx>` object. This object performs a transaction and returns a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`.

You may optionally include a dictionary of :ref:`transaction parameters <transaction-parameters>` as the final argument. If you do not do this, or do not specify a ``from`` value within the parameters, the transaction is sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].transfer(accounts[1], 1e18, {'from': accounts[0]})

    Transaction sent: 0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e
    Token.transfer confirmed - block: 4   gas used: 51019 (33.78%)
    <Transaction object '0x6e557594e657faf1270235bf4b3f27be7f5a3cb8a9c981cfffb12133cbaa165e'>

If you wish to call the contract method without a transaction, use the :func:`ContractTx.call <ContractTx.call>` method.

.. code-block:: python

    >>> Token[0].transfer.call(accounts[1], 1e18, {'from': accounts[0]})
    True

.. _transaction-parameters:

Transaction Parameters
**********************

When executing a transaction to a contract, you can optionally include a :py:class:`dict` of transaction parameters as the final input. It may contain the following values:

    * ``from``: the :func:`Account <brownie.network.account.Account>` that the transaction it sent from. If not given, the transaction is sent from the account that deployed the contract.
    * ``gas_limit``: The amount of gas provided for transaction execution, in wei. If not given, the gas limit is determined using :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>`.
    * ``gas_buffer``: A multiplier applied to :meth:`web3.eth.estimate_gas <web3.eth.Eth.estimateGas>` when setting gas limit automatically. ``gas_limit`` and ``gas_buffer`` cannot be given at the same time.
    * ``gas_price``: The gas price for legacy transaction, in wei. If not given, the gas price is set according to :attr:`web3.eth.gas_price <web3.eth.Eth.gasPrice>`.
    * ``max_fee``: Max fee per gas of dynamic fee transaction.
    * ``priority_fee``: Max priority fee per gas of dynamic fee transaction.
    * ``amount``: The amount of Ether to include with the transaction, in wei.
    * ``nonce``: The nonce for the transaction. If not given, the nonce is set according to :meth:`web3.eth.get_transaction_count <web3.eth.Eth.getTransactionCount>` while taking pending transactions from the sender into account.
    * ``required_confs``: The required :attr:`confirmations<TransactionReceipt.confirmations>` before the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` is processed. If none is given, defaults to 1 confirmation.  If 0 is given, immediately returns a pending :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`, while waiting for a confirmation in a separate thread.
    * ``allow_revert``: Boolean indicating whether the transaction should be broadcasted when it is expected to revert. If not set, the default behaviour is to allow reverting transactions in development and disallow them in a live environment.

All currency integer values can also be given as strings that will be converted by :func:`Wei <brownie.convert.datatypes.Wei>`.

.. hint::

    When working in development environment, the ``from`` field can be any address given as a string. In this way you can broadcast a transaction from an address without having it's private key. It is even possible to send transactions from contracts!

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

.. _core-contracts-live:

Contracts Outside of your Project
=================================

When working in a :ref:`live environment <network-management-live>` or :ref:`forked development network <network-management-fork>`, you can create :func:`Contract <brownie.network.contract.Contract>` objects to interact with already-deployed contracts.

:func:`Contract <brownie.network.contract.Contract>` objects may be created from interfaces within the ``interfaces/`` folder of your project, or by fetching information from a remote source such as a block explorer.

Using Local Interfaces
----------------------

The :func:`InterfaceContainer <brownie.network.contract.InterfaceContainer>` object (available as ``interface``) provides access to the interfaces within your project's ``interfaces/`` folder.

For example, to create a :func:`Contract <brownie.network.contract.Contract>` object from an interface named ``Dai``:

.. code-block:: python

    >>> interface.Dai
    <InterfaceConstructor 'Dai'>

    >>> interface.Dai("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    <Dai Contract object '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

You can also use the :func:`Contract.from_abi <Contract.from_abi>` classmethod to instatiate from an ABI as a dictionary:

.. code-block:: python

    >>> Contract.from_abi("Token", "0x79447c97b6543F6eFBC91613C655977806CB18b0", abi)
    <Token Contract object '0x79447c97b6543F6eFBC91613C655977806CB18b0'>

Fetching from a Remote Source
-----------------------------

Contract objects may also be created by fetching data from a remote source. For example, use :func:`Contract.from_explorer <Contract.from_explorer>` to create an object by querying Etherscan:

.. code-block:: python

    >>> Contract.from_explorer("0x6b175474e89094c44da98b954eedeac495271d0f")
    Fetching source of 0x6B175474E89094C44Da98b954EedeAC495271d0F from api.etherscan.io...
    <Dai Contract '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

Persisting Contracts between Sessions
-------------------------------------

The data used to create :func:`Contract <brownie.network.contract.Contract>` objects is stored in a local database and persists between sessions. After the initial creation via a :ref:`class method <api-network-contract-classmethods>`, you can recreate an object by initializing :func:`Contract <brownie.network.contract.Contract>` with an address:

.. code-block:: python

    >>> Contract("0x6b175474e89094c44da98b954eedeac495271d0f")
    <Dai Contract '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

Alternatively, :func:`Contract.set_alias <Contract.set_alias>` allows you to create an alias for quicker access. Aliases also persist between sessions.

.. code-block:: python

    >>> contract = Contract("0x6b175474e89094c44da98b954eedeac495271d0f")
    >>> contract.set_alias('dai')

    >>> Contract('dai')
    <Dai Contract '0x6B175474E89094C44Da98b954EedeAC495271d0F'>

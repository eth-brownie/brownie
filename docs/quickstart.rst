.. _quickstart:

==========
Quickstart
==========

This page provides a quick overview of how to use Brownie. It relies mostly on examples and assumes a level of familiarity with Python and smart contract development. For more in-depth content, you should read the documentation sections under "Getting Started" in the table of contents.

If you have any questions about how to use Brownie, feel free to ask on `Ethereum StackExchange <https://ethereum.stackexchange.com/>`_ or join us on `Gitter <https://gitter.im/eth-brownie/community>`_.

Creating a New Project
======================

    `Main article:` :ref:`init`

The first step to using Brownie is to initialize a new project. To do this, create an empty folder and then type:

::

    $ brownie init

You can also initialize "`Brownie mixes <https://github.com/brownie-mix>`_", simple templates to build your project upon. For the examples in this document we will use the `token <https://github.com/brownie-mix/token-mix>`_ mix, which is a very basic ERC-20 implementation:

::

    $ brownie bake token

This will create a ``token/`` subdirectory, and download the template project within it.

Exploring the Project
=====================

    `Main article:` :ref:`structure`

Each Brownie project uses the following structure:

    * ``contracts/``: Contract sources
    * ``interfaces/``: Interface sources
    * ``scripts/``: Scripts for deployment and interaction
    * ``tests/``: Scripts for testing the project

The following directories are also created, and used internally by Brownie for managing the project. You should not edit or delete files within these folders.

    * ``build/``: Project data such as compiler artifacts and unit test results
    * ``reports/``: JSON report files for use in the GUI

Compiling your Contracts
========================

    `Main article:` :ref:`compile`

To compile your project:

::

    $ brownie compile

You will see the following output:

::

    Brownie - Python development framework for Ethereum

    Compiling contracts...
    Optimizer: Enabled  Runs: 200
    - Token.sol...
    - SafeMath.sol...
    Brownie project has been compiled at token/build/contracts

You can change the compiler version and optimization settings by editting the :ref:`config file <config-solc>`.

.. note::

    Brownie automatically compiles any new or changed source files each time it is loaded. You do not need to manually run the compiler.

Core Functionality
==================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. It's also a great starting point to familiarize yourself with Brownie's functionality.

The console feels very similar to a regular python interpreter. From inside a project directory, load it by typing:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC client, and give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.

.. hint::

    You can call the builtin :func:`dir <dir>` method to see available methods and attributes for any class. Classes, methods and attributes are highlighted in different colors.

    You can also call :func:`help <help>` on any class or method to view information on it's functionality.

Accounts
--------

    `Main article:` :ref:`core-accounts`

Access to local accounts is through :func:`accounts <brownie.network.account.Accounts>`, a list-like object that contains :func:`Account <brownie.network.account.Account>` objects capable of making transactions.

Here is an example of checking a balance and transfering some ether:

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

Contracts
---------

    `Main article:` :ref:`core-contracts`

Brownie provides a :func:`ContractContainer <brownie.network.contract.ContractContainer>` object for each deployable contract in your project. They are list-like objects used to deploy new contracts.

.. code-block:: python

    >>> Token
    []

    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>

    >>> t = Token.deploy("Test Token", "TST", 18, 1e21, {'from': accounts[1]})

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

When a contact is deployed you are returned a :func:`Contract <brownie.network.contract.ProjectContract>` object that can be used to interact with it. This object is also added to the :func:`ContractContainer <brownie.network.contract.ContractContainer>`.

:func:`Contract <brownie.network.contract.ProjectContract>` objects contain class methods for performing calls and transactions. In this example we are checking a token balance and transfering tokens:

.. code-block:: python

    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

    >>> t.balanceOf(accounts[1])
    1000000000000000000000

    >>> t.transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>

    >>> t.transfer(accounts[2], 1e20, {'from': accounts[1]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 2   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>

    >>> t.balanceOf(accounts[1])
    900000000000000000000

    >>> t.balanceOf(accounts[2])
    100000000000000000000

When a contract source includes `NatSpec documentation <https://solidity.readthedocs.io/en/latest/natspec-format.html>`_, you can view it via the :func:`ContractCall.info <ContractCall.info>` method:

.. code-block:: python

    >>> t.transfer.info()
    transfer(address _to, uint256 _value)
      @dev transfer token for a specified address
      @param _to The address to transfer to.
      @param _value The amount to be transferred.

Transactions
------------

    `Main article:` :ref:`core-transactions`

The :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object contains all relevant information about a transaction, as well as various methods to aid in debugging.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], 1e18, {'from': accounts[0]})

    Transaction sent: 0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753
    Token.transfer confirmed - block: 2   gas used: 51019 (33.78%)

    >>> tx
    <Transaction object '0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753'>

Use :func:`TransactionReceipt.events <TransactionReceipt.events>` to examine the events that fired:

.. code-block:: python

    >>> len(tx.events)
    1

    >>> 'Transfer' in tx.events
    True

    >>> tx.events['Transfer']
    {
        'from': "0x4fe357adbdb4c6c37164c54640851d6bff9296c8",
        'to': "0xfae9bc8a468ee0d8c84ec00c8345377710e0f0bb",
        'value': "1000000000000000000",
    }

To inspect the transaction trace:

.. code-block:: python

    >>> tx.call_trace()
    Call trace for '0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753':
    Token.transfer 0:244  (0x4A32104371b05837F2A36dF6D850FA33A92a178D)
      ├─Token.transfer 72:226
      ├─SafeMath.sub 100:114
      └─SafeMath.add 149:165

For information on why a transaction reverted:

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], 1e18, {'from': accounts[3]})

    Transaction sent: 0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a
    Token.transfer confirmed (reverted) - block: 2   gas used: 23858 (19.26%)
    <Transaction object '0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a'>

    >>> tx.traceback()
    Traceback for '0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a':
    Trace step 99, program counter 1699:
      File "contracts/Token.sol", line 67, in Token.transfer:
        balances[msg.sender] = balances[msg.sender].sub(_value);
    Trace step 110, program counter 1909:
      File "contracts/SafeMath.sol", line 9, in SafeMath.sub:
        require(b <= a);

Writing Scripts
===============

    `Main article:` :ref:`scripts`

You can write scripts to automate contract deployment and interaction. By placing ``from brownie import *`` at the beginning of your script, you can access objects identically to how you would in the console.

To execute the ``main`` function in a script, store it in the ``scripts/`` folder and type:

::

    $ brownie run [script name]

Within the token project, you will find an example script at `scripts/token.py <https://github.com/brownie-mix/token-mix/blob/master/scripts/token.py>`_ that is used for deployment:

.. code-block:: python
    :linenos:

    from brownie import *

    def main():
        Token.deploy("Test Token", "TEST", 18, 1e23, {'from': accounts[0]})

Testing your Project
====================

    `Main article:` :ref:`pytest`

Brownie uses the ``pytest`` framework for contract testing.

Tests should be stored in the ``tests/`` folder.  To run the full suite:

::

    $ brownie test

Fixtures
--------

Brownie provides ``pytest`` fixtures to allow you to interact with your project and to aid in testing. To use a fixture, add an argument with the same name to the inputs of your test function.

Here is an example test function using Brownie's automatically generated fixtures:

.. code-block:: python
    :linenos:

    def test_transfer(Token, accounts):
        token = Token.deploy("Test Token", "TST", 18, 1e20, {'from': accounts[0]})
        assert token.totalSupply() == 1e20

        token.transfer(accounts[1], 1e19, {'from': accounts[0]})
        assert token.balanceOf(accounts[1]) == 1e19
        assert token.balanceOf(accounts[0]) == 9e19

See the :ref:`Pytest Fixtures <pytest-fixtures-reference>` section for a complete list of fixtures.

Handling Reverted Transactions
------------------------------

Transactions that revert raise a :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>` exception. To write assertions around this you can use :func:`brownie.reverts <brownie.test.plugin.RevertContextManager>` as a context manager, which functions very similarly to :func:`pytest.raises <pytest.raises>`:

.. code-block:: python
    :linenos:

    import brownie

    def test_transfer_reverts(accounts, Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e23)
        with brownie.reverts():
            token.transfer(accounts[1], 1e24, {'from': accounts[0]})

You may optionally include a string as an argument. If given, the error string returned by the transaction must match it in order for the test to pass.

.. code-block:: python
    :linenos:

    import brownie

    def test_transfer_reverts(accounts, Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e23)
        with brownie.reverts("Insufficient Balance"):
            token.transfer(accounts[1], 1e24, {'from': accounts[0]})

Isolating Tests
---------------

Test isolation is handled through the :func:`module_isolation <fixtures.module_isolation>` and :func:`fn_isolation <fixtures.fn_isolation>` fixtures:

* :func:`module_isolation <fixtures.module_isolation>` resets the local chain before and after completion of the module, ensuring a clean environment for this module and that the results of it will not affect subsequent modules.
* :func:`fn_isolation <fixtures.fn_isolation>` additionally takes a snapshot of the chain before running each test, and reverts to it when the test completes. This allows you to define a common state for each test, reducing repetitive transactions.

This example uses isolation and a shared setup fixture. Because the ``token`` fixture uses a session scope, the transaction to deploy the contract is only executed once.

.. code-block:: python
    :linenos:

    import pytest
    from brownie import accounts


    @pytest.fixture(scope="module")
    def token(Token):
        yield Token.deploy("Test Token", "TST", 18, 1e20, {'from': accounts[0]})


    def test_transferFrom(fn_isolation, token):
        token.approve(accounts[1], 6e18, {'from': accounts[0]})
        token.transferFrom(accounts[0], accounts[2], 5e18, {'from': accounts[1]})

        assert token.balanceOf(accounts[2]) == 5e18
        assert token.balanceOf(accounts[0]) == 9.5e19
        assert token.allowance(accounts[0], accounts[1]) == 1e18


    def test_balance_allowance(fn_isolation, token):
        assert token.balanceOf(accounts[0]) == 1e20
        assert token.allowance(accounts[0], accounts[1]) == 0


.. _pytest-fixtures-reference:

============================
Fixture and Marker Reference
============================

Brownie includes custom :ref:`fixtures <pytest-fixtures-docs>` and :ref:`markers<pytest-markers-docs>` that can be used when testing your project.

Session Fixtures
================

These fixtures provide quick access to Brownie objects that are frequently used during testing. If you are unfamiliar with these objects, you may wish to read the documentation listed under "Core Functionality" in the table of contents.

.. _test-fixtures-accounts:

.. py:attribute:: accounts

    Yields an :func:`Accounts <brownie.network.account.Accounts>` container for the active project, used to interact with your local accounts.

        .. code-block:: python
            :linenos:

            def test_account_balance(accounts):
                assert accounts[0].balance() == "100 ether"

.. py:attribute:: a

    Short form of the ``accounts`` fixture.

        .. code-block:: python
            :linenos:

            def test_account_balance(a):
                assert a[0].balance() == "100 ether"

.. py:attribute:: chain

    Yields a :func:`Chain <brownie.network.state.Chain>` object, used to access block data and interact with the local test chain.

        .. code-block:: python
            :linenos:

            def test_account_balance(accounts, chain):
                balance = accounts[1].balance()
                accounts[0].transfer(accounts[1], "10 ether")
                assert accounts[1].balance() == balance + "10 ether"

                chain.reset()
                assert accounts[1].balance() == balance

.. py:attribute:: Contract

    Yields the :func:`Contract <brownie.network.contract.Contract>` class, used to interact with contracts outside of the active project.

        .. code-block:: python
            :linenos:

            @pytest.fixture(scope="session")
            def dai(Contract):
                yield Contract.from_explorer("0x6B175474E89094C44Da98b954EedeAC495271d0F")

.. py:attribute:: history

    Yields a :func:`TxHistory <brownie.network.state.TxHistory>` container for the active project, used to access transaction data.

        .. code-block:: python
            :linenos:

            def test_account_balance(accounts, history):
                accounts[0].transfer(accounts[1], "10 ether")
                assert len(history) == 1

.. py:attribute:: interface

    Yields the :func:`InterfaceContainer <brownie.network.contract.InterfaceContainer>` object for the active project, which provides access to project interfaces.

        .. code-block:: python
            :linenos:

            @pytest.fixture(scope="session")
            def dai(interface):
                yield interface.Dai("0x6B175474E89094C44Da98b954EedeAC495271d0F")

.. py:attribute:: pm

    Callable fixture that provides access to :func:`Project <brownie.project.main.Project>` objects, used for testing against installed packages.

        .. code-block:: python
            :linenos:

            @pytest.fixture(scope="module")
            def compound(pm, accounts):
                ctoken = pm('defi.snakecharmers.eth/compound@1.1.0').CToken
                yield ctoken.deploy({'from': accounts[0]})

.. py:attribute:: state_machine

    Yields the :func:`state_machine <brownie.test.stateful.state_machine>` method, used for running a :ref:`stateful test <hypothesis-stateful>`.

        .. code-block:: python
            :linenos:

            def test_stateful(Token, accounts, state_machine):
                token = Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[0]})

                state_machine(StateMachine, accounts, token)

.. py:attribute:: web3

    Yields a :func:`Web3 <brownie.network.web3.Web3>` object.

        .. code-block:: python
            :linenos:

            def test_account_balance(accounts, web3):
                height = web3.eth.block_number
                accounts[0].transfer(accounts[1], "10 ether")
                assert web3.eth.block_number == height + 1

Contract Fixtures
=================

Brownie creates dynamically named fixtures to access each :func:`ContractContainer <brownie.network.contract.ContractContainer>` object within a project. Fixtures are generated for all deployable contracts and libraries.

For example - if your project contains a contract named ``Token``, there will be a ``Token`` fixture available.

    .. code-block:: python
        :linenos:

        def test_token_deploys(Token, accounts):
            token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e24)
            assert token.name() == "Test Token"


Isolation Fixtures
==================

Isolation fixtures are used to ensure a clean test environment when running tests, and to prevent the results of a test from affecting subsequent tests. See :ref:`pytest-fixtures-isolation` for information on how to use these fixtures.

.. py:attribute:: module_isolation

    Resets the local chain before running and after completing the test module.

.. py:attribute:: fn_isolation

    Takes a snapshot of the chain before running a test and reverts to it after the test completes.

.. _pytest-fixtures-reference-markers:

Markers
=======

Brownie provides the following :ref:`markers<pytest-markers-docs>` for use within your tests:

.. py:attribute:: pytest.mark.require_network(network_name)

    Mark a test so that it only runs if the active network is named ``network_name``. This is useful when you have some tests intended for a local development environment and others for a forked mainnet.

        .. code-block:: python
            :linenos:

            @pytest.mark.require_network("mainnet-fork")
            def test_almost_in_prod():
                pass

.. py:attribute:: pytest.mark.no_call_coverage

    Only evaluate coverage for transactions made during this test, not calls.

    This marker is useful for speeding up slow tests that involve many calls to the same view method.

        .. code-block:: python
            :linenos:

            def test_normal(token):
                # during coverage analysis this call is handled as a transaction
                assert token.balanceOf(accounts[0]) == 900

            @pytest.mark.no_call_coverage
            def test_no_call_cov(Token):
                # this call is handled as a call, the test execution is quicker
                assert token.balanceOf(accounts[1]) == 100

.. py:attribute:: pytest.mark.skip_coverage

    Skips a test if coverage evaluation is active.

        .. code-block:: python
            :linenos:

            @pytest.mark.skip_coverage
            def test_heavy_lifting():
                pass

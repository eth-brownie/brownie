.. _hypothesis:

======================
Property-Based Testing
======================

Brownie utilizes the ``hypothesis`` framework to allow for property-based testing.

Much of the content in this section is based on the official `hypothesis.works <https://hypothesis.works/>`_ website. To learn more about property-based testing, you may wish to read this series of `introductory articles <https://hypothesis.works/articles/intro/>`_ or view the official `Hypothesis documentation <https://hypothesis.readthedocs.io/en/latest/>`_.

What is Property-Based Testing?
===============================

Property-based testing is a powerful tool for locating edge cases and discovering faulty assumptions within your code.

The core concept behind property-based testing is that rather than writing a test for a single scenario, you write tests that describe a range of scenarios and then let your computer explore the possibilities for you rather than having to hand-write every one yourself.

The basic process consists of:

    1. Choose a function within your smart contract that you wish to test.
    2. Specify a range of inputs for this function that should always yield the same result.
    3. Call the function with random data from your specification.
    4. Make an assertion about the result.

Using this technique, each test is run many times with different arbitrary data. If an example is found where the assertion fails, an attempt is made to find the simplest case possible that still causes the problem. This example is then `stored in a database <https://hypothesis.readthedocs.io/en/latest/database.html>`_ and repeated in each subsequent tests to ensure that once the issue is fixed, it stays fixed.

Writing Tests
=============

To begin writing property-based tests, import the following two methods:

.. code-block:: python

    from brownie.test import given, strategy

.. py:function:: brownie.test.given

    A decorator for turning a test function that accepts arguments into a randomized test.

    When using Brownie, this is the main entry point to property-based testing. This is a thin wrapper around :func:`hypothesis.given <hypothesis.given>`, the API is identical.

    .. warning::

        Be sure to import ``@given`` from Brownie and not directly from Hypothesis. Importing the function directly can cause issues with test isolation.

.. py:function:: brownie.test.strategy

    A method for creating :ref:`test strategies<hypothesis-strategies>` based on ABI types.

A test using Hypothesis consists of two parts: A function that looks like a normal pytest test with some additional arguments, and a ``@given`` decorator that specifies how to those arguments are provided.

Here is a basic example, testing the ``transfer`` function of an ERC20 token contract.

.. code-block:: python

    from brownie import accounts
    from brownie.test import given, strategy

    @given(value=strategy('uint256', max_value=10000))
    def test_transfer_amount(token, value):
        balance = token.balanceOf(accounts[0])
        token.transfer(accounts[1], value, {'from': accounts[0]})

        assert token.balanceOf(accounts[0]) == balance - value

When this test runs:

    1. The setup phase of all pytest fixtures are executed in their regular order.
    2. A snapshot of the current chain state is taken.
    3. ``strategy`` generates a random integer value and assigns it to the ``amount`` keyword argument.
    4. The test is executed.
    5. The chain is reverted to the snapshot taken in step 2.
    6. Steps 3-5 are repeated 50 times, or until the test fails.
    7. The teardown phase of all pytest fixtures are executed in their normal order.

It is possible to supply multiple strategies via ``@given``. In the following example, we add a ``to`` argument using an address strategy.

.. code-block:: python

    from brownie import accounts
    from brownie.test import given, strategy

    @given(
        to=strategy('address', exclude=accounts[0]),
        value=strategy('uint256', max_value=10000),
    )
    def test_transfer_amount(token, to, value):
        balance = token.balanceOf(accounts[0])
        token.transfer(to, value, {'from': accounts[0]})

        assert token.balanceOf(accounts[0]) == balance - value
        assert token.balanceOf(to) == value

.. _hypothesis-strategies:

Strategies
==========

The key object in every test is a `strategy`. A strategy is a recipe for describing the sort of data you want to generate. Brownie provides a ``strategy`` method that generates strategies for any given ABI type.

.. code-block:: python

    >>> from brownie.test import strategy
    >>> strategy('uint8')
    integers(min_value=0, max_value=255)

Each strategy object contains an ``example`` method that you can call in the console to explore the types of data that will be generated.

.. code-block:: python

    >>> st = strategy('uint8')
    >>> st.example()
    243
    >>> st.example()
    77

``strategy`` accepts different keyword arguments depending on the ABI type.

Type Strategies
---------------

The following strategies correspond to types within `Solidity <https://solidity.readthedocs.io/en/latest/types.html>`_ and `Vyper <https://vyper.readthedocs.io/en/latest/types.html>`_.

Address
*******

    `Base strategy:` :func:`hypothesis.strategies.sampled_from <hypothesis.strategies.sampled_from>`

``address`` strategies yield :func:`Account <brownie.network.account.Account>` objects from the :func:`Accounts <brownie.network.account.Accounts>` container.

Optional keyword arguments:

    * ``length``: The number of :func:`Account <brownie.network.account.Account>` objects to include in the strategy. If the :func:`Accounts <brownie.network.account.Accounts>` container holds less than this number of objects, the entire container is used.
    * ``excludes``: An object, iterable or callable used to filter strategy results.

.. code-block:: python

    >>> strategy('address')
    sampled_from(accounts)

    >>> strategy('address').example()
    <Account '0x33A4622B82D4c04a53e170c638B944ce27cffce3'>

Bool
****

    `Base strategy:` :func:`hypothesis.strategies.booleans <hypothesis.strategies.booleans>`

``bool`` strategies yield ``True`` or ``False``.

This strategy does not accept any keyword arguments.

.. code-block:: python

    >>> strategy('bool')
    booleans()

    >>> strategy('bool').example()
    True

Bytes
*****

    `Base strategy:` :func:`hypothesis.strategies.binary <hypothesis.strategies.binary>`

``bytes`` strategies yield byte strings.

All ``bytes`` strategies accept the following keyword arguments:

    * ``excludes``: An object, iterable or callable used to filter strategy results.

For `fixed length values <https://solidity.readthedocs.io/en/latest/types.html#fixed-size-byte-arrays>`_ (``bytes1`` ... ``bytes32``) the strategy always generates bytes of exactly the given length. For `dynamic bytes arrays <https://solidity.readthedocs.io/en/latest/types.html#bytes-and-strings-as-arrays>`_ (``bytes``), the minimum and maximum length may be specified using keyord arguments:

    * ``min_size``: Minimum length for each returned value. The default value is ``1``.
    * ``max_size``: Maximum length for each returned value. The default value is ``64``.

.. code-block:: python

    >>> strategy('bytes32')
    binary(min_size=32, max_size=32)
    >>> strategy('bytes', max_size=16)
    binary(min_size=1, max_size=16)

    >>> strategy('bytes8').example()
    b'\xb8\xd6\xaa\xcbR\x0f\xb88'

Decimal
*******

    `Base strategy:` :func:`hypothesis.strategies.decimals <hypothesis.strategies.decimals>`

``decimal`` strategies yield :py:class:`decimal.Decimal <decimal.Decimal>` instances.

Optional keyword arguments:

    * ``min_value``: The maximum value to return. The default is ``-2**127`` (the lower bound of Vyper's ``decimal`` type). The given value is converted to :func:`Fixed <brownie.convert.datatypes.Fixed>`.
    * ``max_value``: The maximum value to return. The default is ``2**127-1`` (the upper bound of Vyper's ``decimal`` type). The given value is converted to :func:`Fixed <brownie.convert.datatypes.Fixed>`.
    * ``places``: The number of decimal points to include. The default value is ``10``.
    * ``excludes``: An object, iterable or callable used to filter strategy results.


.. code-block:: python

    >>> strategy('decimal')
    decimals(min_value=-170141183460469231731687303715884105728, max_value=170141183460469231731687303715884105727, places=10)

    >>> strategy('decimal').example()
    Decimal('44.8234019327')

Integer
*******

    `Base strategy:` :func:`hypothesis.strategies.integers <hypothesis.strategies.integers>`

``int`` and ``uint`` strategies yield integer values.

Optional keyword arguments:

    * ``min_value``: The maximum value to return. The default is the lower bound for the given type. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`.
    * ``max_value``: The maximum value to return. The default is the upper bound for the given type. The given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`.
    * ``excludes``: An object, iterable or callable used to filter strategy results.

.. code-block:: python

    >>> strategy('uint32')
    integers(min_value=0, max_value=4294967295)
    >>> strategy('int8')
    integers(min_value=-128, max_value=127)
    >>> strategy('uint', min_value="1 ether", max_value="25 ether")
    integers(min_value=1000000000000000000, max_value=25000000000000000000)

    >>> strategy('uint').example()
    156806085

String
******

    `Base strategy:` :func:`hypothesis.strategies.text <hypothesis.strategies.text>`

``string`` strategies yield unicode text strings.

Optional keyword arguments:

    * ``min_size``: Minimum length for each returned value. The default value is ``0``.
    * ``max_size``: Maximum length for each returned value. The default value is ``64``.
    * ``excludes``: An object, iterable or callable used to filter strategy results.

.. code-block:: python

    >>> strategy('string')
    text(max_size=64)
    >>> strategy('string', min_size=12, max_size=23)
    text(min_size=12, max_size=23)

    >>> strategy('string').example()
    '\x02\x14\x01\U0009b3c5'

Sequence Strategies
-------------------

Along with the core strategies, Brownie also offers strategies for generating array or tuple sequences.

Array
*****

    `Base strategy:` :func:`hypothesis.strategies.lists <hypothesis.strategies.lists>`

Array strategies yield lists of strategies for the base array type. It is possible to generate arrays of both fixed and dynamic length, as well as multidimensional arrays.

Optional keyword arguments:

    * ``min_length``: The minimum number of items inside a dynamic array. The default value is ``1``.
    * ``max_length``: The maximum number of items inside a dynamic array. The default value is ``8``.
    * ``unique``: If ``True``, each item in the list will be unique.

For multidimensional dynamic arrays, ``min_length`` and ``max_length`` may be given as a list where the length is equal to the number of dynamic dimensions.

You can also include keyword arguments for the base type of the array. They will be applied to every item within the generated list.

.. code-block:: python

    >>> strategy('uint32[]')
    lists(elements=integers(min_value=0, max_value=4294967295), min_length=1, max_length=8)
    >>> strategy('uint[3]', max_value=42)
    lists(elements=integers(min_value=0, max_value=42), min_length=3, max_length=3)

    >>> strategy('uint[3]', max_value=42).example()
    [16, 23, 14]

Tuple
*****

    `Base strategy:` :func:`hypothesis.strategies.tuples <hypothesis.strategies.tuples>`

Tuple strategies yield tuples of mixed strategies according to the given type string.

This strategy does not accept any keyword arguments.

.. code-block:: python

    >>> strategy('(int16,bool)')
    tuples(integers(min_value=-32768, max_value=32767), booleans())
    >>> strategy('(uint8,(bool,bytes4))')
    tuples(integers(min_value=0, max_value=255), tuples(booleans(), binary(min_size=4, max_size=4)))

    >>> strategy('(uint16,bool)').example()
    (47628, False)

Contract Strategies
-------------------

The ``contract_strategy`` function is used to draw from :func:`ProjectContract <brownie.network.contract.ProjectContract>` objects within a :func:`ContractContainer <brownie.network.contract.ContractContainer>`.


.. py:function:: brownie.test.contract_strategy(contract_name)

    `Base strategy:` :func:`hypothesis.strategies.sampled_from <hypothesis.strategies.sampled_from>`

    A strategy to access :func:`ProjectContract <brownie.network.contract.ProjectContract>` objects.

    * ``contract_name``: The name of the contract, given as a string

    .. code-block:: python

        >>> ERC20
        [<ERC20 Contract '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87'>, <ERC20 Contract '0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6'>]

        >>> from brownie.test import contract_strategy
        >>> contract_strategy('ERC20')
        sampled_from(ERC20)

        >>> contract_strategy('ERC20').example()
        <ERC20 Contract '0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6'>



Other Strategies
----------------

All of the strategies that Brownie provides are based on core strategies from the ``hypothesis.strategies`` library. If you require something more specific or complex than Brownie offers, you can also directly use hypothesis strategies.

See the `Hypothesis strategy documentation <https://hypothesis.readthedocs.io/en/latest/data.html#>`_ for more information on available strategies and how they can be customized.

.. _hypothesis-settings:

Settings
========

Depending on the scope and complexity of your tests, it may be necessary to modify the default settings for how property-based tests are run.

The mechanism for doing this is the :py:class:`hypothesis.settings <hypothesis.settings>` object. You can set up a ``@given`` based test to use this using a settings decorator:


.. code-block:: python

    from brownie.test import given
    from hypothesis import settings

    @given(strategy('uint256'))
    @settings(max_examples=500)
    def test_this_thoroughly(x):
        pass


You can also affect the settings permanently by adding a ``hypothesis`` field to your project's ``brownie-config.yaml`` file:

.. code-block:: yaml

    hypothesis:
        max_examples: 500

 See the :ref:`Configuration File<config>` documentation for more information.

Available Settings
------------------

.. note::

    See the Hypothesis `settings documentation <https://hypothesis.readthedocs.io/en/latest/settings.html#available-settings>`_ for a complete list of available settings. This section only lists settings where the default value has been changed from the Hypothesis default.

.. py:attribute:: deadline

    The number of milliseconds that each individual example within a test is allowed to run. Tests that take longer than this time will be considered to have failed.

    Because Brownie test times can vary widely, this property has been disabled by default.

    default-value: ``None``

.. py:attribute:: max_examples

    The maximum number of times a test will be run before considering it to have passed.

    For tests involving many complex transactions you may wish to reduce this value.

    default-value: ``50``

.. py:attribute:: report_multiple_bugs

    Because Hypothesis runs each test many times, it can sometimes find multiple bugs in a single run. Reporting all of them at once can be useful, but also produces significantly longer and less descriptive output when compared to reporting a single error.

    default-value: ``False``

.. py:attribute:: stateful_step_count

    The maximum number of rules to execute in a stateful program before ending the run and considering it to have passed.

    For more complex state machines you may wish to increase this value - however you should keep in mind that this can result in siginificantly longer execution times.

    default-value: ``10``

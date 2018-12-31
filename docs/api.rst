.. _api:

===========
Brownie API
===========

The following classes and methods are available when developing brownie scripts or using the console.

Eth
===

These classes and methods relate to the Ethereum blockchain:

.. py:class:: web3

    Brownie implementation of ``web3py.web3``. Only some class methods are exposed. See the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`__ for more information.

.. py:class:: TransactionReceipt

    An instance of this class is returned whenever a transaction is completed. Contains a combination of values from ``web3.eth.getTransaction`` and ``web3.eth.getTransactionReceipt``.

.. py:classmethod:: TransactionReceipt.info()

    Provides verbose information about the transaction.

    ::

        >>> tx = accounts[0].transfer(accounts[1], 100)
        <Transaction object '0x2facf2d1d2fdfa10956b7beb89cedbbe1ba9f4a2f0592f8a949d6c0318ec8f66'>
        >>> tx.info()

        Transaction was Mined
        ---------------------
        Tx Hash: 0x2facf2d1d2fdfa10956b7beb89cedbbe1ba9f4a2f0592f8a949d6c0318ec8f66
        From: 0x5fe657e72E76E7ACf73EBa6FA07ecB40b7312d80
        To: 0x5814fC82d51732c412617Dfaecb9c05e3B823253
        Value: 100
        Function Signature: 0x0
        Block: 1
        Gas Used: 21000

.. _wei:

.. py:method:: wei(value)

    Converts a value to wei. Useful for strings where you specify the unit, or for large floats given in scientific notation, where a direct conversion to ``int`` would cause inaccuracy from floating point errors.

    ``wei`` is automatically applied in all Brownie methods when an input is meant to specify an amount of ether.

    Some examples:

    .. code-block:: python

        >>> wei("1 ether")
        1000000000000000000
        >>> wei("12.49 gwei")
        12490000000
        >>> wei("0.029 shannon")
        29000000
        >>> wei(8.38e32)
        838000000000000000000000000000000

.. py:exception:: VirtualMachineError

    Raised whenever a transaction results in an EVM exception.

.. py:attribute:: VirtualMachineError.revert_msg

    Contains the EVM revert error message, if any.

Console
=======

These methods are used in the console.

.. py:method:: logging(tx = None, exc = None)

    Adjusts the logging verbosity. See :ref:`config` for more information on logging levels.

.. py:method:: reset(network = None)

    Reboots the local RPC client and resets the brownie environment. You can also optionally switch to a different network.

.. py:method:: run(script)

    Runs a deployment script. See :ref:`deploy` for more information.

Accounts
========

Account classes are not meant to be instantiated directly. The ``Accounts`` container is available as ``accounts`` and will create each ``Account`` automatically during initialization. Add more accounts using ``Accounts.add``.

.. py:class:: Accounts

    Singleton container that holds all of the available accounts as ``Account`` or ``LocalAccount`` objects. This is a sub-type of ``list`` so all list methods are also available.

.. py:classmethod:: Accounts.add(priv_key)

    Creates a new ``LocalAccount`` with private key ``priv_key``, appends it to the container, and returns the new account instance.

.. py:classmethod:: Accounts.at(address)

    Given an address, returns the corresponding ``Account`` or ``LocalAccount`` from the container.

.. py:class:: Account

    An ethereum address that you control the private key for, and so can send transactions from. It is a sub-class of ``str``, so if given as a method argument it will be interpreted as the public address.

.. py:attribute:: Account.address

    The public address of the account. Viewable by printing the class, you do not need to call this attribute directly.

.. py:attribute:: Account.nonce

    The current nonce of the address.

.. py:classmethod:: Account.balance()

    Returns the current balance at the address, in wei.

.. py:classmethod:: Account.estimate_gas(to, amount, data="")

    Estimates the gas required to perform a transaction. Raises a ``VirtualMachineError`` if the transaction would revert.

.. py:classmethod:: Account.transfer(to, amount, gas=None, gas_price=None)

    Transfers ether.

    * ``to``: Recipient address.
    * ``amount``: Amount to send, in wei_.
    * ``gas``: Gas limit, in wei_. If none is given, the price is set using ``web3.eth.estimateGas``.
    * ``gas_price``: Gas price, in wei_. If none is given, the price is set using ``web3.eth.gasPrice``.

    Returns a ``TransactionReceipt`` instance.

.. py:classmethod:: Account.deploy(contract, *args)

    Deploys a contract.

    * ``contract``: A ``ContractDeployer`` instance of the contract to be deployed.
    * ``*args``: Contract constructor arguments.
    * ``**kwargs``: Addresses for any required libraries.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    Returns a ``Contract`` instance.

.. py:class:: LocalAccount

    Functionally identical to ``Account``. The only difference is that a ``LocalAccount`` is one where the private key was directly inputted, and so is not found in ``web3.eth.accounts``.

Contracts
=========

Contract classes are not meant to be instantiated directly. Each ``ContractDeployer`` instance is created automatically during when Brownie starts. New ``Contract`` instances are created via methods in the deployer.

.. py:class:: ContractDeployer

    A container class that holds all Contracts of the same type, and is used to deploy new instances of that contract.

.. py:attribute:: ContractDeployer.abi

    The ABI of the contract.

.. py:attribute:: ContractDeployer.bytecode

    The bytecode of the contract, without any applied constructor arguments.

.. py:attribute:: ContractDeployer.signatures

    A dictionary of bytes4 signatures for each contract method.

    .. code-block:: python

        >>> Token.signatures.keys()
        dict_keys(['name', 'approve', 'totalSupply', 'transferFrom', 'decimals', 'balanceOf', 'symbol', 'transfer', 'allowance'])
        >>> Token.signatures['transfer']
        0xa9059cbb

.. py:attribute:: ContractDeployer.topics

    A dictionary of bytes32 topics for each contract event.

    .. code-block:: python

        >>> Token.topics.keys()
        dict_keys(['Transfer', 'Approval'])
        >>> Token.topics['Transfer']
        0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef

.. py:classmethod:: ContractDeployer.list()

    Returns a list of every deployed contract instance in the container.

.. py:classmethod:: ContractDeployer.deploy(account, *args, **kwargs)

    Deploys the contract.

    * ``account``: An ``Account`` instance to deploy the contract from.
    * ``*args``: Contract constructor arguments.
    * ``**kwargs``: Addresses for any required libraries.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    Returns a ``Contract`` instance.

.. py:classmethod:: ContractDeployer.at(address, owner=None)

    Returns a ``Contract`` instance.

    * ``address``: Address where the contract is deployed. Raises a ValueError if there is no bytecode at the address.
    * ``owner``: ``Account`` instance to set as the contract owner. If transactions to the contract do not specify a ``'from'`` value, they will be sent from this account.

.. py:class:: Contract

    A deployed contract. This class allows you to call or send transactions to the contract. It is a sub-class of ``str``, so if given as a method argument it will be interpreted as the public address.

.. py:attribute:: Contract.tx

    The ``TransactionReceipt`` of the transaction that deployed the contract. If the contract was not deployed during this instance of brownie, it will be ``None``.

.. py:attribute:: Contract.bytecode

    The bytecode of the deployed contract, including constructor arguments.

.. py:classmethod:: Contract.balance()

    Returns the balance at the contract address, in wei.

.. py:class:: ContractCall(*args)

    Calls a contract method that does not require a transaction, and returns the result. ``args`` must match the required inputs for the method.

    The expected inputs are shown in the method's ``__repr__`` value.

    .. code-block:: python

        >>> Token[0].allowance
        <ContractCall object 'allowance(address,address)'>
        >>> Token[0].allowance(accounts[0], accounts[2])
        0

.. py:class:: Contract.ContractTx(*args)

    A contract method that requires a transaction in order to call.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    .. code-block:: python

        >>> Token[0].transfer
        <ContractTx object 'transfer(address,uint256)'>
        >>> Token[0].transfer(accounts[1], 100000, {'from':accounts[0]})

        Transaction sent: 0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0
        Transaction confirmed - block: 2   gas spent: 51049
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>

.. _api_check:

Check
=====

The check module exposes the following methods that are used in place of ``assert`` when writing Brownie tests. All check methods raise an ``AssertionError`` when they fail.

.. py:method:: check.true(statement, fail_msg = "Expected statement to be true")

    Raises if ``statement`` does not evaluate to True.

.. py:method:: check.false(statement, fail_msg = "Expected statement to be False")

    Raises if ``statement`` does not evaluate to False.

.. py:method:: check.reverts(fn, args, fail_msg = "Expected transaction to revert", revert_msg=None)

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call does not cause the EVM to throw an exception.

    If ``revert_msg`` is not ``None``, the check will only pass if the EVM reverts with a specific message.

.. py:method:: check.confirms(fn, args, fail_msg = "Expected transaction to confirm")

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call causes the EVM to throw an exception.

    Used if you want to give a specific error message for this function. If you do not require one, you can simply attempt the call and the test will still fail if the call throws.

.. py:method:: check.equal(a, b, fail_msg = "Expected values to be equal")

    Raises if ``a != b``.

.. py:method:: check.not_equal(a, b, fail_msg = "Expected values to be not equal")

    Raises if ``a == b``.

.. _api_alert:

Alert
=====

The alert module is used to set up notifications and callbacks based on state changes in the blockchain.

.. py:class:: Alert(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None)

    An alert object. It is active immediately upon creation of the instance.

    * ``fn``: A callable to check for the state change.
    * ``args``: Arguments to supply to the callable.
    * ``kwargs``: Keyword arguments to supply to the callable.
    * ``delay``: Number of seconds to wait between checking for changes.
    * ``msg``: String to display upon change. The string will have ``.format(initial_value, new_value)`` applied before displaying.
    * ``callback``: A callback function to call upon a change in value. It should accept two arguments, the initial value and the new value.

.. py:classmethod:: Alert.stop()

    Stops the alert.

.. py:method:: new(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None)

    Alias for creating a new alert.

.. py:method:: show()

    Returns a list of all currently active alerts.

.. py:method:: stop_all()

    Stops all currently active alerts.

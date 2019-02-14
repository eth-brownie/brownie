.. _api:

===========
Brownie API
===========

The following classes and methods are available when writing brownie scripts or using the console.

From the console you can call ``dir`` to see available methods and attributes for any class. By default, callables are highlighed in cyan and attributes in blue. You can also call ``help`` on any class or method to view information on it's functionality.

Eth
===

These classes and methods relate to the Ethereum blockchain and test RPC:

.. py:class:: web3

    Brownie implementation of ``web3py.web3``. Only some class methods are exposed. See the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`__ for more information.

.. _rpc:

.. py:class:: Rpc

    Exposes methods for interacting with ``ganache-cli`` when running a local RPC environment. When using the console or writing tests, an instance of this class is available as ``rpc``.

.. py:classmethod:: Rpc.time()

    Returns the current epoch time in the RPC as an integer.

.. py:classmethod:: Rpc.sleep(seconds)

    Advances the RPC time. You can only advance the time by whole seconds.

.. py:classmethod:: Rpc.mine(blocks = 1)

    Forces new blocks to be mined.

.. py:classmethod:: Rpc.snapshot()

    Creates a snapshot at the current block height.

.. py:classmethod:: Rpc.revert()

    Reverts the blockchain to the latest snapshot. Raises ``ValueError`` if no snapshot has been taken.

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

Console
=======

These methods are used in the console.

.. py:method:: gas(*args)

    Displays or sets the default gas limit.

    * If an integer value is given, this will be the default gas limit.
    * If set to "auto", None, True or False, the gas limit is determined
      automatically.

    .. note:: When the gas limit is calculated automatically, transactions that would revert will raise a VirtualMachineError during the gas estimation and so will not be broadcasted.

.. py:method:: logging(tx = None, exc = None)

    Adjusts the logging verbosity. See :ref:`config` for more information on logging levels.

.. py:method:: reset(network = None)

    Reboots the local RPC client and resets the brownie environment. You can also optionally switch to a different network.

.. py:method:: run(script)

    Loads a script and runs the ``main`` method within it. See :ref:`deploy` for more information.


Transactions
============

.. py:class:: TransactionReceipt

    An instance of this class is returned whenever a transaction is broadcasted. When printed in the console, they will appear yellow if the transaction is still pending or red if the transaction caused the EVM to revert.

    Many of the attributes will be set to ``None`` while the transaction is still pending.

.. py:attribute:: TransactionReceipt.block_number

    The block height at which the transaction confirmed.

.. py:attribute:: TransactionReceipt.contract_address

    The address of the contract deployed as a result of this transaction, if any.

.. py:attribute:: TransactionReceipt.events

    A dictionary of decoded event logs for this transaction. If you are connected to an RPC client that allows for ``debug_traceTransaction``, event data is still available when the transaction reverts.

.. py:attribute:: TransactionReceipt.fn_name

    The name of the contract and function called by the transaction.

.. py:attribute:: TransactionReceipt.gas_limit

    The gas limit of the transaction, in wei.

.. py:attribute:: TransactionReceipt.gas_price

    The gas price of the transaction, in wei.

.. py:attribute:: TransactionReceipt.gas_used

    The amount of gas consumed by the transaction, in wei.

.. py:attribute:: TransactionReceipt.input

    The complete calldata of the transaction.

.. py:attribute:: TransactionReceipt.logs

    The unencrypted event logs for the transaction. Not available if the transaction reverts.

.. py:attribute:: TransactionReceipt.nonce

    The nonce of the transaction.

.. py:attribute:: TransactionReceipt.receiver

    The address the transaction was sent to, as a string.

.. py:attribute:: TransactionReceipt.revert_msg

    The error string returned when a transaction causes the EVM to revert, if any.

.. py:attribute:: TransactionReceipt.return_value

    The value returned from the called function, if any. Only available if the RPC client allows ``debug_traceTransaction``.

.. py:attribute:: TransactionReceipt.sender

    The address the transaction was sent from. Where possible, this will be an Account instance instead of a string.

.. py:attribute:: TransactionReceipt.status

    The status of the transaction: -1 for pending, 0 for failed, 1 for success.

.. py:attribute:: TransactionReceipt.trace

    The structLog from the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#debug_tracetransaction>`__ RPC method. If you are using Infura this attribute is not available.

    Along with the standard data, the structLog also contains the following additional information:

    * ``address``: The address of the contract that executed this opcode
    * ``contractName``: The name of the contract
    * ``fn``: The name of the function
    * ``jumpDepth``: The number of jumps made since entering this contract. The initial function has a value of 1.
    * ``source``: The start and end offset of the source code associated with this opcode.

.. py:attribute:: TransactionReceipt.txid

    The transaction hash.

.. py:attribute:: TransactionReceipt.txindex

    The integer of the transaction's index position in the block.

.. py:attribute:: TransactionReceipt.value

    The value of the transaction, in wei.

.. py:classmethod:: TransactionReceipt.info()

    Displays verbose information about the transaction, including event logs and the error string if a transaction reverts.

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
        Block: 1
        Gas Used: 21000

.. py:classmethod:: TransactionReceipt.call_trace()

    Displays the sequence of contracts and functions called while executing this transaction, and the structLog index where each call or jump occured. Any functions that terminated with a ``REVERT`` opcode are highlighted in red.

    ::

        >>> tx = Token[0].transferFrom(accounts[2], accounts[3], "10000 ether")

        Transaction sent: 0x0d96e8ceb555616fca79dd9d07971a9148295777bb767f9aa5b34ede483c9753
        Token.transferFrom confirmed (reverted) - block: 4   gas used: 25425 (26.42%)

        >>> tx.call_trace()
        Token.transferFrom 0 (0x4C2588c6BFD533E0a27bF7572538ca509f31882F)
        Token.sub 86 (0x4C2588c6BFD533E0a27bF7572538ca509f31882F)

.. py:classmethod:: TransactionReceipt.error()

    Displays the source code that caused the first revert in the transaction, if any.

    ::

        >>> tx.error()
        File "contracts/SafeMath.sol", line 9:

                c = a + b;
                require(c >= a);
            }
            function sub(uint a, uint b) internal pure returns (uint c) {
                require(b <= a);
                c = a - b;
            }
            function mul(uint a, uint b) internal pure returns (uint c) {
                c = a * b;

.. py:exception:: VirtualMachineError

    Raised when a call to a contract causes an EVM exception.  Transactions that result in a revert will still return a TransactionReceipt instead of raising.

.. py:attribute:: VirtualMachineError.revert_msg

    Contains the EVM revert error message, if any.

Accounts
========

Account classes are not meant to be instantiated directly. The ``Accounts`` container is available as ``accounts`` and will create each ``Account`` automatically during initialization. Add more accounts using ``Accounts.add``.

.. py:class:: Accounts

    Singleton list-like container that holds all of the available accounts as ``Account`` or ``LocalAccount`` objects.

.. py:classmethod:: Accounts.add(priv_key)

    Creates a new ``LocalAccount`` with private key ``priv_key``, appends it to the container, and returns the new account instance.  If no private key is entered, one is randomly generated.

.. py:classmethod:: Accounts.at(address)

    Given an address, returns the corresponding ``Account`` or ``LocalAccount`` from the container.

.. py:classmethod:: Accounts.mnemonic(phrase, count=10)

    Generates ``LocalAccount`` instances from a seed phrase based on the BIP44 standard. Compatible with `MetaMask <https://metamask.io>`__ and other popular wallets.

.. py:classmethod:: Accounts.remove(address)

    Removes an address from the container. The address may be given as a string or an ``Account`` instance.

.. py:classmethod:: Accounts.clear()

    Empties the container.

.. py:class:: Account

    An ethereum address that you control the private key for, and so can send transactions from.

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

    * ``contract``: A ``ContractContainer`` instance of the contract to be deployed.
    * ``*args``: Contract constructor arguments.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument.

    Returns a ``Contract`` instance upon success. If the transaction reverts or you do not wait for a confirmation, a ``TransactionReceipt`` is returned instead.

.. py:class:: LocalAccount

    Functionally identical to ``Account``. The only difference is that a ``LocalAccount`` is one where the private key was directly inputted, and so is not found in ``web3.eth.accounts``.

.. py:attribute:: LocalAccount.public_key

    The local account's public key.

.. py:attribute:: LocalAccount.private_key

    The local account's private key.

Contracts
=========

Contract classes are not meant to be instantiated directly. Each ``ContractContainer`` instance is created automatically during when Brownie starts. New ``Contract`` instances are created via methods in the deployer.

.. py:class:: ContractContainer

    A container class that holds all Contracts of the same type, and is used to deploy new instances of that contract.

.. py:attribute:: ContractContainer.abi

    The ABI of the contract.

.. py:attribute:: ContractContainer.bytecode

    The bytecode of the contract, without any applied constructor arguments.

.. py:attribute:: ContractContainer.signatures

    A dictionary of bytes4 signatures for each contract method.

    .. code-block:: python

        >>> Token.signatures.keys()
        dict_keys(['name', 'approve', 'totalSupply', 'transferFrom', 'decimals', 'balanceOf', 'symbol', 'transfer', 'allowance'])
        >>> Token.signatures['transfer']
        0xa9059cbb

.. py:attribute:: ContractContainer.topics

    A dictionary of bytes32 topics for each contract event.

    .. code-block:: python

        >>> Token.topics.keys()
        dict_keys(['Transfer', 'Approval'])
        >>> Token.topics['Transfer']
        0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef

.. py:classmethod:: ContractContainer.deploy(account, *args)

    Deploys the contract.

    * ``account``: An ``Account`` instance to deploy the contract from.
    * ``*args``: Contract constructor arguments.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    If the contract requires a library, the most recently deployed one will be used. If the required library has not been deployed yet an ``IndexError`` is raised.

    Returns a ``Contract`` instance upon success. If the transaction reverts or you do not wait for a confirmation, a ``TransactionReceipt`` is returned instead.

.. py:classmethod:: ContractContainer.at(address, owner=None)

    Returns a ``Contract`` instance.

    * ``address``: Address where the contract is deployed. Raises a ValueError if there is no bytecode at the address.
    * ``owner``: ``Account`` instance to set as the contract owner. If transactions to the contract do not specify a ``'from'`` value, they will be sent from this account.

.. py:classmethod:: ContractContainer.remove(address)

    Removes a contract instance from the container.

.. py:class:: Contract

    A deployed contract. This class allows you to call or send transactions to the contract.

.. py:attribute:: Contract.tx

    The ``TransactionReceipt`` of the transaction that deployed the contract. If the contract was not deployed during this instance of brownie, it will be ``None``.

.. py:attribute:: Contract.bytecode

    The bytecode of the deployed contract, including constructor arguments.

.. py:classmethod:: Contract.balance()

    Returns the balance at the contract address, in wei.

.. py:class:: ContractCall(*args)

    Calls a non state-changing contract method without broadcasting a transaction, and returns the result. ``args`` must match the required inputs for the method.

    The expected inputs are shown in the method's ``__repr__`` value.

    .. code-block:: python

        >>> Token[0].allowance
        <ContractCall object 'allowance(address,address)'>
        >>> Token[0].allowance(accounts[0], accounts[2])
        0

.. py:attribute:: ContractCall.abi

    The contract ABI specific to this method.

.. py:attribute:: ContractCall.signature

    The bytes4 signature of this method.

.. py:classmethod:: ContractCall.transact(*args)

    Sends a transaction to the method and returns a ``TransactionReceipt``.

.. py:class:: ContractTx(*args)

    Sends a transaction to a potentially state-changing contract method. Returns a ``TransactionReceipt``.

    You can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

    .. code-block:: python

        >>> Token[0].transfer
        <ContractTx object 'transfer(address,uint256)'>
        >>> Token[0].transfer(accounts[1], 100000, {'from':accounts[0]})

        Transaction sent: 0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0
        Transaction confirmed - block: 2   gas spent: 51049
        <Transaction object '0xac54b49987a77805bf6bdd78fb4211b3dc3d283ff0144c231a905afa75a06db0'>

.. py:attribute:: ContractTx.abi

    The contract ABI specific to this method.

.. py:attribute:: ContractTx.signature

    The bytes4 signature of this method.

.. py:classmethod:: ContractTx.call(*args)

    Calls the contract method without broadcasting a transaction, and returns the result.

.. _api_check:

Check
=====

The check module exposes the following methods that are used in place of ``assert`` when writing Brownie tests. All check methods raise an ``AssertionError`` when they fail.

.. py:method:: check.true(statement, fail_msg = "Expected statement to be true")

    Raises if ``statement`` does not evaluate to True.

.. py:method:: check.false(statement, fail_msg = "Expected statement to be False")

    Raises if ``statement`` does not evaluate to False.

.. py:method:: check.reverts(fn, args, fail_msg = "Expected transaction to revert", revert_msg=None)

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call does not cause the EVM to revert. This check will work regardless of if the revert happens from a call or a transaction.

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

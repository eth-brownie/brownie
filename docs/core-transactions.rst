.. _core-transactions:

=====================================
Inspecting and Debugging Transactions
=====================================

Each time your perform a transaction you are returned a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`. This object contains all relevant information about the transaction, as well as various methods to aid in debugging.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], "1 ether", {'from': accounts[0]})

    Transaction sent: 0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b
    Token.transfer confirmed - block: 2   gas used: 51019 (33.78%)

    >>> tx
    <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>

To view human-readable information on a transaction, call the :func:`TransactionReceipt.info <TransactionReceipt.info>` method.

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
====================

Data about events is available as :func:`TransactionReceipt.events <TransactionReceipt.events>`. It is stored in an :func:`EventDict <brownie.network.event.EventDict>` object; a hybrid container with both dict-like and list-like properties.

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

Use it as a dictionary for looking at specific events when the sequence they are fired in does not matter:

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

.. _debug:

Debugging Failed Transactions
=============================

.. note::

    Debugging functionality relies on the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`_ RPC method. If you are using Infura this endpoint is unavailable. Attempts to access this functionality will raise an ``RPCRequestError``.

When a transaction reverts in the console you are still returned a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`, but it will show as reverted. If an error string is given, it will be displayed in brackets and highlighted in red.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], "1 ether", {'from': accounts[3]})

    Transaction sent: 0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a
    Token.transfer confirmed (Insufficient Balance) - block: 2   gas used: 23858 (19.26%)
    <Transaction object '0x5ff198f3a52250856f24792889b5251c120a9ecfb8d224549cb97c465c04262a'>

The error string is also available as :func:`TransactionReceipt.revert_msg <TransactionReceipt.revert_msg>`.

.. code-block:: python

    >>> tx.revert_msg
    'Insufficient Balance'

You can also call :func:`TransactionReceipt.traceback <TransactionReceipt.traceback>` to view a python-like traceback for the failing transaction. It shows source highlights at each jump leading up to the revert.

.. code-block:: python

    >>> tx.traceback()
    Traceback for '0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4':
    Trace step 169, program counter 3659:
        File "contracts/SecurityToken.sol", line 156, in SecurityToken.transfer:
        _transfer(msg.sender, [msg.sender, _to], _value);
    Trace step 5070, program counter 5666:
        File "contracts/SecurityToken.sol", lines 230-234, in SecurityToken._transfer:
        _addr = _checkTransfer(
            _authID,
            _id,
            _addr
        );
    Trace step 5197, program counter 9719:
        File "contracts/SecurityToken.sol", line 136, in SecurityToken._checkTransfer:
        require(balances[_addr[SENDER]] >= _value, "Insufficient Balance");

Inspecting the Transaction Trace
================================

The Trace Object
----------------

The best way to understand exactly happened in a transaction is to generate and examine a `transaction trace <https://github.com/ethereum/go-ethereum/wiki/Tracing:-Introduction#user-content-basic-traces>`_. This is available as a list of dictionaries at :func:`TransactionReceipt.trace <TransactionReceipt.trace>`, with several fields added to make it easier to understand.

Each step in the trace includes the following data:

.. code-block:: javascript

    {
        'address': "",  // address of the contract containing this opcode
        'contractName': "",  // contract name
        'depth': 0,  // the number of external jumps away the initially called contract (starts at 0)
        'error': "",  // occurred error
        'fn': "",  // function name
        'gas': 0,  // remaining gas
        'gasCost': 0,  // cost to execute this opcode
        'jumpDepth': 1,  // number of internal jumps within the active contract (starts at 1)
        'memory': [],  // execution memory
        'op': "",  // opcode
        'pc': 0,  // program counter
        'source': {
            'filename': "path/to/file.sol",  // path to contract source
            'offset': [0, 0]  // start:stop offset associated with this opcode
        },
        'stack': [],  // execution stack
        'storage': {}  // contract storage
    }

Call Traces
-----------

When dealing with complex transactions the trace can be may thousands of steps long - it can be challenging to know where to begin when examining it. Brownie provides the :func:`TransactionReceipt.call_trace <TransactionReceipt.call_trace>` method to view a complete map of every jump that occured in the transaction, along with associated trace indexes:

.. code-block:: python

    >>> tx.call_trace()
    Call trace for '0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4':
    SecurityToken.transfer 0:5198  (0xea53cB8c11f96243CE3A29C55dd9B7D761b2c0BA)
    └─SecurityToken._transfer 170:5198
        ├─IssuingEntity.transferTokens 608:4991  (0x40b49Ad1B8D6A8Df6cEdB56081D51b69e6569e06)
        │ ├─IssuingEntity.checkTransfer 834:4052
        │ │ ├─IssuingEntity._getID 959:1494
        │ │ │ └─KYCRegistrar.getID 1186:1331  (0xa79269260195879dBA8CEFF2767B7F2B5F2a54D8)
        │ │ ├─IssuingEntity._getID 1501:1635
        │ │ ├─IssuingEntity._getID 1642:2177
        │ │ │ └─KYCRegistrar.getID 1869:2014  (0xa79269260195879dBA8CEFF2767B7F2B5F2a54D8)
        │ │ ├─IssuingEntity._getInvestors 2305:3540
        │ │ │ └─KYCRegistrar.getInvestors 2520:3483  (0xa79269260195879dBA8CEFF2767B7F2B5F2a54D8)
        │ │ │   ├─KYCBase.isPermitted 2874:3003
        │ │ │   │ └─KYCRegistrar.isPermittedID 2925:2997
        │ │ │   └─KYCBase.isPermitted 3014:3143
        │ │ │     └─KYCRegistrar.isPermittedID 3065:3137
        │ │ └─IssuingEntity._checkTransfer 3603:4037
        │ ├─IssuingEntity._setRating 4098:4162
        │ ├─IssuingEntity._setRating 4204:4268
        │ ├─SafeMath32.add 4307:4330
        │ └─IssuingEntity._incrementCount 4365:4770
        │   ├─SafeMath32.add 4400:4423
        │   ├─SafeMath32.add 4481:4504
        │   ├─SafeMath32.add 4599:4622
        │   └─SafeMath32.add 4692:4715
        └─SecurityToken._checkTransfer 5071:5198


Each line shows the following information:

::

    ContractName.functionName start:stop


Where ``start`` and ``stop`` are the indexes of :func:`TransactionReceipt.trace <TransactionReceipt.trace>` where the function was entered and exited. If an address is also shown, it means the function was entered via an external jump. Functions that terminated with ``REVERT`` or ``INVALID`` opcodes are highlighted in red.

:func:`TransactionReceipt.call_trace <TransactionReceipt.call_trace>` provides an initial high level overview of the transaction execution path, which helps you to examine the individual trace steps in a more targetted manner.

Accessing Transaction History
=============================

The :func:`TxHistory <brownie.network.state.TxHistory>` container, available as ``history``, holds all the transactions that have been broadcasted. You can use it to access :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects if you did not assign them a unique name when making the call.

.. code-block:: python

    >>> history
    [<Transaction object '0xe803698b0ade1598c594b2c73ad6a656560a4a4292cc7211b53ffda4a1dbfbe8'>, <Transaction object '0xa7616a96ef571f1791586f570017b37f4db9decb1a5f7888299a035653e8b44b'>]

Unconfirmed Transactions
========================

After broadcasting a transaction, Brownie will pause and wait for it to confirm. If you are using the console you can press ``Ctrl-C`` stop waiting and immediately receive the :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object. It will be marked as pending, and many attributes and methods will not yet be available. A notification will be displayed when the transaction confirms.

If you send another transaction from the same account before the previous one has confirmed, it is still broadcast with the next sequential nonce.

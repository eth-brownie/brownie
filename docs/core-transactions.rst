.. _core-transactions:

=====================================
Inspecting and Debugging Transactions
=====================================

The :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` object provides information about a transaction, as well as various methods to aid in debugging.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], 1e18, {'from': accounts[0]})

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

Event Data
==========

Data about events is available as :func:`TransactionReceipt.events <TransactionReceipt.events>`. It is stored in an :func:`EventDict <brownie.network.event.EventDict>` object; a hybrid container with both dict-like and list-like properties.

.. hint::

    You can also view events that were emitted in a reverted transaction. When debugging it can be useful to create temporary events to examine local variables during the execution of a failed transaction.

.. code-block:: python

    >>> tx.events
    {
        'CountryModified': [
            {
                'country': 1,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            },
            {
                'country': 2,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
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

    # name of the address
    >>> tx.events[1].name
    'CountryModified'

    # address where the event fired
    >>> tx.events[1].address
    "0xDd18d6475A7C71Ee33CEBE730a905DbBd89945a1"

    >>> tx.events[1]
    {
        'country': 1,
        'limits': (0, 0, 0, 0, 0, 0, 0, 0),
        'minrating': 1,
        'permitted': True
    }

Internal Transactions and Deployments
=====================================

:func:`TransactionReceipt.internal_transfers <TransactionReceipt.new_contracts>` provides a list of internal ether transfers that occurred during the transaction.

.. code-block:: python

        >>> tx.internal_transfers
        [
            {
                "from": "0x79447c97b6543F6eFBC91613C655977806CB18b0",
                "to": "0x21b42413bA931038f35e7A5224FaDb065d297Ba3",
                "value": 100
            }
        ]

:func:`TransactionReceipt.new_contracts <TransactionReceipt.new_contracts>` provides a list of addresses for any new contracts that were created during a transaction. This is useful when you are using a factory pattern.

.. code-block:: python

    >>> deployer
    <Deployer Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

    >>> tx = deployer.deployNewContract()
    Transaction sent: 0x6c3183e41670101c4ab5d732bfe385844815f67ae26d251c3bd175a28604da92
      Gas price: 0.0 gwei   Gas limit: 79781
      Deployer.deployNewContract confirmed - Block: 4   Gas used: 79489 (99.63%)

    >>> tx.new_contracts
    ["0x1262567B3e2e03f918875370636dE250f01C528c"]

To generate :func:`Contract <brownie.network.contract.ProjectContract>` objects from this list, use :func:`ContractContainer.at <ContractContainer.at>`:

.. code-block:: python

    >>> tx.new_contracts
    ["0x1262567B3e2e03f918875370636dE250f01C528c"]
    >>> Token.at(tx.new_contracts[0])
    <Token Contract object '0x1262567B3e2e03f918875370636dE250f01C528c'>

.. _debug:

Debugging Failed Transactions
=============================

.. note::

    Debugging functionality relies on the `debug_traceTransaction <https://geth.ethereum.org/docs/rpc/ns-debug#debug_tracetransaction>`_ RPC method. If you are using Infura this endpoint is unavailable. Attempts to access this functionality will raise an ``RPCRequestError``.

When a transaction reverts in the console you are still returned a :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`, but it will show as reverted. If an error string is given, it will be displayed in brackets and highlighted in red.

.. code-block:: python

    >>> tx = Token[0].transfer(accounts[1], 1e18, {'from': accounts[3]})

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

Inspecting the Trace
====================

The Trace Object
----------------

The best way to understand exactly happened in a transaction is to generate and examine a `transaction trace <https://geth.ethereum.org/docs/dapp/tracing#basic-traces>`_. This is available as a list of dictionaries at :func:`TransactionReceipt.trace <TransactionReceipt.trace>`, with several fields added to make it easier to understand.

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

When dealing with complex transactions the trace can be thousands of steps long - it can be challenging to know where to begin examining it. Brownie provides the :func:`TransactionReceipt.call_trace <TransactionReceipt.call_trace>` method to view a complete map of every jump that occured in the transaction:

.. code-block:: python

    >>> tx.call_trace()
    Call trace for '0x7824c6032966ca2349d6a14ec3174d48d546d0fb3020a71b08e50c7b31c1bcb1':
    Initial call cost  [21228 gas]
    LiquidityGauge.deposit  0:3103  [64010 / 128030 gas]
    ├── LiquidityGauge._checkpoint  83:1826  [-6420 / 7698 gas]
    │   ├── GaugeController.get_period_timestamp  [STATICCALL]  119:384  [2511 gas]
    │   ├── ERC20CRV.start_epoch_time_write  [CALL]  411:499  [1832 gas]
    │   ├── GaugeController.gauge_relative_weight_write  [CALL]  529:1017  [3178 / 7190 gas]
    │   │   └── GaugeController.change_epoch  697:953  [2180 / 4012 gas]
    │   │       └── ERC20CRV.start_epoch_time_write  [CALL]  718:806  [1832 gas]
    │   └── GaugeController.period  [STATICCALL]  1043:1336  [2585 gas]
    ├── LiquidityGauge._update_liquidity_limit  1929:2950  [45242 / 54376 gas]
    │   ├── VotingEscrow.balanceOf  [STATICCALL]  1957:2154  [2268 gas]
    │   └── VotingEscrow.totalSupply  [STATICCALL]  2180:2768  [6029 / 6866 gas]
    │       └── VotingEscrow.supply_at  2493:2748  [837 gas]
    └── ERC20LP.transferFrom  [CALL]  2985:3098  [1946 gas]

Each line shows the following information:

::

    ContractName.functionName (external call opcode) start:stop [internal / total gas used]

Where ``start`` and ``stop`` are the indexes of :func:`TransactionReceipt.trace <TransactionReceipt.trace>` where the function was entered and exited. :func:`TransactionReceipt.call_trace <TransactionReceipt.call_trace>` provides an initial high level overview of the transaction execution path, which helps you to examine the individual trace steps in a more targetted manner and determine where things went wrong in a complex transaction.

Functions that terminated with ``REVERT`` or ``INVALID`` opcodes are highlighted in red.

For functions with no subcalls, the used gas is shown. Otherwise, the first gas number is the amount of gas used internally by this function and the second number is the total gas used by the function including all sub-calls. Gas refunds from deleting storage or contracts are shown as negative gas used. Note that overwriting an existing zero-value with another zero-value will incorrectly display a gas refund.

Calling :func:`TransactionReceipt.call_trace <TransactionReceipt.call_trace>` with ``True`` as an argument provides an expanded view:

.. code-block:: python

    >>> history[-1].call_trace(True)

    Call trace for '0x7824c6032966ca2349d6a14ec3174d48d546d0fb3020a71b08e50c7b31c1bcb1':
    Initial call cost  [21228 gas]
    LiquidityGauge.deposit  0:3103  [64010 / 128030 gas]
    ├── LiquidityGauge._checkpoint  83:1826  [-6420 / 7698 gas]
    │   │
    │   ├── GaugeController.get_period_timestamp  [STATICCALL]  119:384  [2511 gas]
    │   │       ├── address: 0x0C41Fc429cC21BC3c826efB3963929AEdf1DBb8e
    │   │       ├── input arguments:
    │   │       │   └── p: 0
    │   │       └── return value: 1594574319
    ...

The expanded trace includes information about external subcalls, including:

* the target address
* the amount of ether transferred
* input arguments
* return values

For calls that revert, the revert reason is given in place of the return value:

.. code-block:: python

    >>> history[-1].call_trace(True)
    ...
    └── ERC20LP.transferFrom  [CALL]  2985:3098  [1946 gas]
            ├── address: 0xd495633B90a237de510B4375c442C0469D3C161C
            ├── value: 0
            ├── input arguments:
            │   ├── _from: 0x9EC9431CCCCD2C73F0A2F68DC69A4A527AB5D809
            │   ├── _to: 0x5AE569698C5F986665018B6E1D92A71BE71DEF9A
            │   └── _value: 100000
            └── revert reason: Integer underflow

You can also access this information programmatically via the :func:`TransactionReceipt.subcalls <TransactionReceipt.subcalls>` attribute:

.. code-block:: python

    >>> history[-1].subcalls
    [
        {
            'from': "0x5AE569698C5F986665018B6e1d92A71be71DEF9a",
            'function': "get_period_timestamp(int128)",
            'inputs': {
                'p': 0
            },
            'op': "STATICCALL",
            'return_value': (1594574319,),
            'to': "0x0C41Fc429cC21BC3c826efB3963929AEdf1DBb8e"
        },
    ...

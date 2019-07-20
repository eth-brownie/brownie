.. _debug:

===============
Debugging Tools
===============

When using the console, transactions that revert still return a :ref:`api-network-tx` object. This object provides access to various attributes and methods that help you determine why it reverted.

.. note:: Debugging functionality relies on the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`__ RPC method. If you are using Infura this endpoint is unavailable. Attempts to access this functionality will raise an ``RPCRequestError``.

Revert Strings
==============

The first step in determining why a transaction has failed is to look at the error string it returned (the "revert string").  This is available as ``TransactionReceipt.revert_msg``, and is also displayed in the console output when the transaction confirms. Often this alone will be enough to understand what has gone wrong.

.. code-block:: python

    >>> tx = token.transfer(accounts[1], 11000, {'from': accounts[0]})

    Transaction sent: 0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4
    SecurityToken.transfer confirmed (Insufficient Balance) - block: 13   gas used: 226266 (2.83%)
    <Transaction object '0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4'>

    >>> tx.revert_msg
    'Insufficient Balance'

A good coding practice is to use one expression per ``require`` so your revert strings can be more precise.  For example, if a transaction fails from the following require statement you cannot immediately tell whether it failed because of the balance or the allowance:

.. code-block:: solidity

    function transferFrom(address _from, address _to, uint _amount) external returns (bool) {
        require (allowed[_from][msg.sender] >= _amount && balance[_from] >= _amount);

By seperating the ``require`` expressions, unique revert strings are possible and determining the cause becomes trivial:

.. code-block:: solidity

    function transferFrom(address _from, address _to, uint _amount) external returns (bool) {
        require (allowed[_from][msg.sender] >= _amount, "Insufficient allowance");
        require (balance[_from][] >= _amount, "Insufficient Balance");

Contract Source Code
====================

You can call ``TransactionReceipt.error()`` to display the section of the contract source that caused the revert. Note that in some situations, particiarly where an ``INVALID`` opcode is raised, the source may not be available.

.. code-block:: python

    >>> tx.error()
    Trace step 5197, program counter 9719:
        File "contracts/SecurityToken.sol", line 136, in SecurityToken._checkTransfer:
        require(balances[_addr[SENDER]] >= _value, "Insufficient Balance");

Sometimes the source that reverted is insufficient to determine what went wrong, for example if a SafeMath ``require`` failed. In this case you can call ``TransactionReceipt.traceback()`` to view a python-like traceback for the failing transaction. It shows source highlights at each jump leading up to the revert.

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

Events
======

Brownie provides access to events that fired in reverted transactions. They are viewable via ``TransactionReceipt.events`` in the same way as events for successful transactions. If you cannot determine why a transaction reverted or are getting unexpected results, one approach is to add temporary logging events into your code to see the values of different variables during execution.

See the :ref:`events<event-data>` section of :ref:`interaction` for information on event data is stored.

The Transaction Trace
=====================

The best way to understand exactly happened in a failing transaction is to generate and examine the `transaction trace <https://github.com/ethereum/go-ethereum/wiki/Tracing:-Introduction#user-content-basic-traces>`_. This is available as a list of dictionaries at ``TransactionReceipt.trace``, with several fields added to make it easier to understand.

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
===========

Because the trace is often many thousands of steps long, it can be challenging to know where to begin when examining it. Brownie provides the ``TransactionReceipt.call_trace()`` method to view a complete map of every jump that occured in the transaction, along with associated trace indexes:

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

Each line shows the active contract and function name, the trace indexes where the function is entered and exitted, and an address if the function was entered via an external jump. Functions that terminated with ``REVERT`` or ``INVALID`` opcodes are highlighted in red.

Calling ``call_trace`` provides an initial high level overview of the transaction execution path, which helps you to examine the individual trace steps in a more targetted manner.

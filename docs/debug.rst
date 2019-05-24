.. _debug:

===============
Debugging Tools
===============

.. note:: Debugging functionality relies on the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#user-content-debug_tracetransaction>`__ RPC method. If you are using Infura this endpoint is unavailable. Attempts to access this functionality will raise an ``RPCRequestError``.

When a transaction reverts in the console you are still returned a ``TransactionReceipt``. From this object you can call the following attributes and methods to help determine why it reverted:

* ``TransactionReceipt.trace``: The call trace structLog as a list.
* ``TransactionReceipt.revert_msg``: The error string returned when the EVM reverted, if any.
* ``TransactionReceipt.events``: The events that were emitted before the transaction reverted.
* ``TransactionReceipt.error()``: Displays the filename, line number, and lines of code that caused the revert.
* ``TransactionReceipt.call_trace()``: Displays the sequence of contracts and functions called while executing this transaction, and the structLog list index where each call or jump occured. Any functions that terminated with a ``REVERT`` opcode are highlighted in red.

See the :ref:`api-network-tx` section of the API documentation for more detailed information.


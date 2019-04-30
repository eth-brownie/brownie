===============
Debugging Tools
===============

.. note:: Debugging functionality relies on the `debug_traceTransaction <https://github.com/ethereum/go-ethereum/wiki/Management-APIs#debug_tracetransaction>`__ RPC method. If you are using Infura this attribute is not available.

When a transaction reverts and the gas limit is not set to automatic, you are still returned a ``TransactionReceipt``. From this instance you can call the following attributes and methods to help determine why it reverted:

* ``TransactionReceipt.revert_msg``: The error string returned when the EVM reverted, if any.
* ``TransactionReceipt.trace``: The call trace structLog as a list.
* ``TransactionReceipt.events``: The events that were emitted before the transaction reverted.
* ``TransactionReceipt.error()``: Displays the filename, line number, and line of code that caused the revert.
* ``TransactionReceipt.call_trace()``: Displays the sequence of contracts and functions called while executing this transaction, and the structLog list index where each call or jump occured. Any functions that terminated with a ``REVERT`` opcode are highlighted in red.

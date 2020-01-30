=======
Brownie
=======

Brownie is a Python-based development and testing framework for smart contracts targeting the `Ethereum Virtual Machine <https://solidity.readthedocs.io/en/v0.6.0/introduction-to-smart-contracts.html#the-ethereum-virtual-machine>`_.

.. note::

    All code starting with ``$`` is meant to be run on your terminal. Code starting with ``>>>`` is meant to run inside the Brownie console.

.. note::

    This project relies heavily upon ``web3.py`` and the documentation assumes a basic familiarity with it. You may wish to view the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`_ if you have not used it previously.

Features
========

* Full support for `Solidity <https://github.com/ethereum/solidity>`_ and `Vyper <https://github.com/vyperlang/vyper>`_
* Contract testing via `pytest <https://github.com/pytest-dev/pytest>`_, including trace-based coverage evaluation
* Powerful debugging tools, including python-style tracebacks and custom error strings
* Built-in console for quick project interaction
* Support for `ethPM <https://www.ethpm.com>`_ packages

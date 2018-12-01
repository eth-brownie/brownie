=======
Brownie
=======

Brownie is a simple python framework for ethereum smart contract testing.

.. warning::
    This project is still in early development and should be considered a beta. Future changes may break existing functionality.

Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__
* `py-solc <https://github.com/ethereum/py-solc>`__
* `web3py <https://github.com/ethereum/web3.py>`__

Installation
============

**Ubuntu**

::

    curl https://github.com/iamdefinitelyahuman/brownie-install.sh | sh

Quick Usage
===========

To set up the default folder and file structure for brownie use:

::

    brownie init

From there, type ``brownie`` for basic usage information.

See the :ref:`quickstart` section for a more in depth tutorial to get you familiar with Brownie.

Table of Contents
=================

.. toctree::   :maxdepth: 2

    init.rst
    quickstart.rst
    deploy.rst
    test.rst
    console.rst

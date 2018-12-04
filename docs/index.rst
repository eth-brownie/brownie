=======
Brownie
=======

Brownie is a simple python framework for ethereum smart contract testing.

.. note::
    All code starting with ``$`` is meant to be run on your terminal. Code starting with ``>>>`` is meant to run inside the Brownie console.

.. warning::
    This project is still in early development and should be considered a beta. Future changes may break existing functionality.

Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__
* `py-solc <https://github.com/ethereum/py-solc>`__
* `web3py <https://github.com/ethereum/web3.py>`__

.. note:: This project relies heavily upon Web3.py. This documentation assumes a basic familiarity with it. You may wish to view the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`__ if you have not used it previously.

Installation
============

**Ubuntu**

.. code-block:: bash

    $ curl https://github.com/iamdefinitelyahuman/brownie-install.sh | sh

Quick Usage
===========

To set up the default folder and file structure for brownie use:

.. code-block:: bash

    $ brownie init

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
    config.rst

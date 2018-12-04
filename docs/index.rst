=======
Brownie
=======

Brownie is a simple python framework for testing, deploying and interacting with ethereum smart contracts.

.. note::
    All code starting with ``$`` is meant to be run on your terminal. Code starting with ``>>>`` is meant to run inside the Brownie console.

.. warning::
    This project is still in development and should be considered a beta. Future changes may break existing functionality.

Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__
* `Python 3.7 <https://www.python.org/downloads/release/python-371/>`__ (and python3-dev)
* `solc <https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages>`__


Installation
============

**Ubuntu**

This installs brownie at ``/usr/local/lib/brownie/`` and creates a virtual environment with all the required packages.

::

    $ curl https://raw.githubusercontent.com/iamdefinitelyahuman/brownie/master/brownie-install.sh | sh

Quick Usage
===========

To set up the default folder and file structure for brownie use:

::

    $ brownie init

From there, type ``brownie`` for basic usage information.

See the :ref:`quickstart` section for a more in depth tutorial to get you familiar with Brownie.

Table of Contents
=================

.. toctree::   :maxdepth: 2

    quickstart.rst
    init.rst
    deploy.rst
    test.rst
    console.rst
    persist.rst
    config.rst
    api.rst

.. _install:

==================
Installing Brownie
==================

The easiest way to install Brownie is via pip.

::

    $ pip install eth-brownie

You can also clone the `github repository <https://github.com/HyperLink-Technology/brownie>`__ and use setuptools for the most up-to-date version.

::

    $ python3 setup.py install

Once you have installed, type ``brownie`` to verify that it worked:

.. parsed-literal::

    $ brownie
    Brownie |release| - Python development framework for Ethereum

    Usage:  brownie <command> [<args>...] [options <args>]

Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`__
* `pip <https://pypi.org/project/pip/>`__
* `python3 <https://www.python.org/downloads/release/python-368/>`__ version 3.6 or greater, python3-dev, python3-tk

As brownie relies on `py-solc-x <https://github.com/iamdefinitelyahuman/py-solc-x>`__, you do not need solc installed locally but you must install all required `solc dependencies <https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages>`__.

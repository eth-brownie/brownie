.. _install:

==================
Installing Brownie
==================

The easiest way to install Brownie is via pip.

::

    $ pip install eth-brownie

You can also clone the `github repository <https://github.com/iamdefinitelyahuman/brownie>`_ and use setuptools for the most up-to-date version.

::

    $ python3 setup.py install

Once you have installed, type ``brownie`` to verify that it worked:

::

    $ brownie
    Brownie - Python development framework for Ethereum

    Usage:  brownie <command> [<args>...] [options <args>]

Dependencies
============

Brownie has the following dependencies:

* `ganache-cli <https://github.com/trufflesuite/ganache-cli>`_ - tested with version `6.8.2 <https://github.com/trufflesuite/ganache-cli/releases/tag/v6.8.2>`_
* `pip <https://pypi.org/project/pip/>`_
* `python3 <https://www.python.org/downloads/release/python-368/>`_ version 3.6 or greater, python3-dev

As brownie relies on `py-solc-x <https://github.com/iamdefinitelyahuman/py-solc-x>`_, you do not need solc installed locally but you must install all required `solc dependencies <https://solidity.readthedocs.io/en/latest/installing-solidity.html#binary-packages>`_.


.. _install-tk:

Tkinter
-------

:ref:`The Brownie GUI<gui>` is built using the `Tk GUI toolkit <https://tcl.tk/>`_. Both Tk and `tkinter <https://docs.python.org/3.8/library/tkinter.html>`_ are available on most Unix platforms, as well as on Windows systems.

Tk is not a strict dependency for Brownie. However, if it is not installed on your system you will receive an error when attempting to load the GUI.

You can use the following command to check that Tk has been correctly installed:

::

    $ python -m tkinter

This should open a simple window and display the installed version number.

For installation instructions read `Installing TK <https://tkdocs.com/tutorial/install.html>`_ within the TK Documentation.
